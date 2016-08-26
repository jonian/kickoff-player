import requests

from lxml import html
from fuzzywuzzy import fuzz
from operator import itemgetter
from handlers.data import DataHandler
from handlers.cache import CacheHandler


class StreamsportsApi:

	def __init__(self):
		self.cache = CacheHandler()
		self.data = DataHandler()

		self.headers = { 'User-Agent': 'Mozilla/5.0' }
		self.base_url = 'http://www.streamsports.co'
		self.fixtures = self.data.load_today_fixtures()

	def cache_key(self, url):
		if not url:
			url = 'home'

		key = url.replace(self.base_url + '/', '')
		key = key.strip('/').strip('-')
		key = 'StreamSports:' + key

		return key

	def get(self, url=''):
		cache_key = self.cache_key(url)

		try:
			response = self.cache.load(cache_key)

			if response is None:
				response = requests.get(self.base_url + '/' + url, headers=self.headers)

				if response.status_code == 200:
					self.cache.save(cache_key, response.content, 300)

			response = response.content
		except Exception:
			response = '<html><body></body></html>'

		response = html.fromstring(response)

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
			link = stream.xpath('.//td[6]//a')[0].attrib['href'].strip()

			if link:
				items.append({ 'host': host, 'rate': rate, 'language': lang, 'url': link })

		return items

	def save_events(self):
		items = []

		for fixture in self.fixtures:
			data = self.get_fixture_match(fixture)

			if not data is None:
				streams = self.get_event_streams(data['url'])

				for item in streams:
					item['fixture'] = fixture.id
					items.append(item)

		if len(items) > 0:
			self.data.set_multiple('event', items, 'url')

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

		sort = sorted(items, key=itemgetter('ratio-1'), reverse=True)[0]

		if sort['ratio-1'] > 80 and sort['ratio-2'] > 70:
			return sort['event']

		return None
