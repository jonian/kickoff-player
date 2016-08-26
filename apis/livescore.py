from lxml import html
from fuzzywuzzy import fuzz
from operator import itemgetter
from selenium import webdriver
from handlers.data import DataHandler


class LivescoreApi:

	def __init__(self):
		self.data = DataHandler()
		self.fixtures = self.data.load_live_fixtures()

		self.webdriver = webdriver.PhantomJS()
		self.webdriver.get('http://livescore.com/soccer')

		self.page_source = self.webdriver.page_source
		self.webdriver.quit()

		self.document = html.fromstring(self.page_source)

	def get_stage_list(self):
		items = []

		for item in self.document.xpath('//div[@data-type="stg"]'):
			sid = item.attrib['data-stg-id']
			lnk = item.xpath('.//a')

			if sid.isdigit() and len(lnk) > 0:
				name = lnk[0].text_content().split('::')[0].strip()
				span = lnk[-1].xpath('.//span')

				if len(span) > 0:
					stg = span[-1].text_content().split('::')[0].strip()
				else:
					stg = lnk[-1].text_content().split('::')[0].strip()

				items.append({ 'id': sid, 'name': name, 'stage': stg })

		return items

	def get_event_list(self):
		items = []

		for event in self.document.xpath('//div[@data-type="evt"]'):
			eid = event.attrib['data-id'].split('-')[-1]
			sid = event.attrib['data-stg-id']

			if eid.isdigit() and sid.isdigit():
				minute = event.xpath('.//div[contains(@class, "min")]//span')[0].text_content().strip()
				score = event.xpath('.//div[contains(@class, "sco")]')[0].text_content().strip()

				if ':' in minute:
					minute = None

				if '?' in score:
					score = None

				home = event.xpath('.//div[contains(@class, "ply")]')[0].text_content().strip()
				away = event.xpath('.//div[contains(@class, "ply")]')[-1].text_content().strip()

				items.append({
					'id': eid, 'stage_id': sid,
					'min': minute, 'score': score,
					'home': home, 'away': away
				})

		return items

	def update_fixtures(self):
		items = []

		for fixture in self.fixtures:
			data = self.get_fixture_match(fixture)

			if not data is None:
				item = { 'api_id': fixture.api_id }

				if not data['min'] is None:
					item['minute'] = data['min']

				if not data['score'] is None:
					item['home_team_goals'] = int(data['score'].split('-')[0])
					item['away_team_goals'] = int(data['score'].split('-')[-1])

				if len(item.items()) > 1:
					items.append(item)

		if len(items) > 0:
			self.data.set_multiple('fixture', items)

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
