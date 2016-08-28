from lxml import html
from fuzzywuzzy import fuzz
from operator import itemgetter
from handlers.data import DataHandler
from helpers.utils import cached_request


class StreamsportsApi:

	def __init__(self):
		self.data = DataHandler()
		self.fixtures = self.data.load_today_fixtures()

	def get(self, url=''):
		response = cached_request(url=url, base_url='streamsports.co', ttl=300)
		response = response if response is None else html.fromstring(response)

		return response

	def get_event_list(self):
		data = self.get('football')
		items = []

		for event in data.xpath('//table[contains(@class, "stream-table")]//tbody//tr'):
			home = event.xpath('.//td[4]//strong')[0].text_content().strip()
			away = event.xpath('.//td[4]//strong')[1].text_content().strip()
			link = event.xpath('.//td[5]//a')[0].attrib['href'][1:].strip()

			items.append({ 'home': home, 'away': away, 'url': link })

		return items

	def get_event_streams(self, url):
		data = self.get(url)
		items = []

		for stream in data.xpath('//table[@id="streamsTable"]//td[text()="P2P"]//parent::tr'):
			rate = stream.xpath('.//td[2]')[0].text_content().strip()
			host = stream.xpath('.//td[3]')[0].text_content().split(' ')[0].strip()
			lang = stream.xpath('.//td[4]')[0].text_content().split(' ')[0].strip()
			link = stream.xpath('.//td[6]//a')[0].attrib['href']

			if link and rate and host and lang:
				lang = str(lang)[:3].upper()
				rate = int(rate.replace('Kbps', ''))

				items.append({ 'host': host, 'rate': rate, 'language': lang, 'url': link })

		return items

	def save_events(self):
		items = []

		for fixture in self.fixtures:
			data = self.get_fixture_match(fixture)

			if not data is None:
				streams = self.get_event_streams(data['url'])

				for stream in streams:
					stream = self.data.set_single('stream', stream, 'url')

					items.append({
						'fs_id': str(fixture.id) + '_' + str(stream.id),
						'fixture': fixture.id,
						'stream': stream.id,
					})

		if len(items) > 0:
			self.data.set_multiple('event', items, 'fs_id')

	def get_fixture_match(self, fixture):
		items = []
		home = fixture.home_team
		away = fixture.away_team

		for event in self.get_event_list():
			home_ratio = [
				fuzz.ratio(home.name, event['home']),
				fuzz.ratio(home.short_name, event['home'])
			]
			away_ratio = [
				fuzz.ratio(away.name, event['away']),
				fuzz.ratio(away.short_name, event['away'])
			]
			ratio = sorted(home_ratio + away_ratio, reverse=True)

			items.append({ 'ratio-1': ratio[0], 'ratio-2': ratio[1], 'event': event })

		if len(items) > 0:
			sort = sorted(items, key=itemgetter('ratio-1'), reverse=True)[0]

			if sort['ratio-1'] > 80 and sort['ratio-2'] > 70:
				return sort['event']

		return None
