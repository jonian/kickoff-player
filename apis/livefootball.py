from lxml import html
from fuzzywuzzy import fuzz
from operator import itemgetter
from helpers.utils import cached_request


class LivefootballApi:

	def __init__(self, data, cache):
		self.data = data
		self.cache = cache

	def get(self, url='', ttl=86400):
		base_url = 'livefootballol.me'
		response = cached_request(url=url, cache=self.cache, base_url=base_url, ttl=ttl)
		response = response if response is None else html.fromstring(response)

		return response

	def parse_name(self, name):
		name = name.replace('Sopcast', '')
		name = name.replace('SopCast', '')
		name = name.replace('Acestream', '')
		name = name.replace('AceStream', '')
		name = name.strip()

		return name

	def get_host_links(self):
		data = self.get()
		items = []

		if data is None:
			return items

		try:
			bar = data.xpath('//div[contains(@class, "headerbar")]')[0]
			ace = bar.xpath('.//a//span[text()="AceStream"]//parent::a')[0]
			ace = ace.attrib['href']
			sop = bar.xpath('.//a//span[text()="Sopcast"]//parent::a')[0]
			sop = sop.attrib['href']

			items.append({ 'name': 'AceStream', 'url': ace })
			items.append({ 'name': 'SopCast', 'url': sop })
		except (IndexError, ValueError):
			pass

		return items

	def get_host_channels(self, url):
		data = self.get(url)
		items = []

		if data is None:
			return items

		for stream in data.xpath('//div[@id="system"]//article//table//tr'):
			try:
				link = stream.xpath('.//td[2]//a')[0]
				link = link.attrib['href']
				name = stream.xpath('.//td[2]//strong')[0]
				name = name.text_content()

				if 'sopcast' in name.lower():
					lang = stream.xpath('.//td[5]')[0]
				else:
					lang = stream.xpath('.//td[4]')[0]

				name = self.parse_name(name)
				lang = lang.text_content().strip()
				lang = 'Unknown' if lang == '' else lang.title()

				items.append({
					'name': name,
					'language': lang,
					'url': link
				})
			except (IndexError, ValueError):
				pass

		return items

	def get_host_streams(self, url):
		data = self.get(url)
		items = []

		if data is None:
			return items

		try:
			root = data.xpath('//div[@id="system"]//table')[0]
			lang = root.xpath('.//td[text()="Language"]//following-sibling::td[1]')[0]
			lang = lang.text_content().strip()
			lang = 'Unknown' if lang == '' else lang
			rate = root.xpath('.//td[text()="Bitrate"]//following-sibling::td[1]')[0]
			rate = rate.text_content().strip()
			rate = 0 if rate == '' else int(rate.replace('Kbps', ''))

			item = {
				'rate': rate,
				'language': lang,
				'lang': lang[:3].upper(),
				'host': None,
				'url': None,
				'hd_url': None
			}

			for link in root.xpath('.//a'):
				href = link.attrib['href']
				host = href.split('://')[0]
				text = link.getparent().text_content()

				if host in ['acestream', 'sop']:
					item['host'] = 'Sopcast' if host == 'sop' else 'Acestream'

					if 'HD' in text:
						item['hd_url'] = href
					else:
						item['url'] = href

			if item['url'] is not None:
				items.append(item)
		except (IndexError, ValueError):
			pass

		return items

	def get_events_link(self):
		data = self.get()
		link = None

		if data is None:
			return link

		try:
			hbar = data.xpath('//div[contains(@class, "headerbar")]')[0]
			link = hbar.xpath('.//a//span[text()="Football"]//parent::a')[0]
			link = link.attrib['href']
		except (IndexError, ValueError):
			pass

		return link

	def get_events_links(self, url):
		data = self.get(url)
		items = []

		if data is None:
			return items

		for link in data.xpath('//div[@id="system"]//a[contains(@href, "/streaming/")]'):
			try:
				items.append(link.attrib['href'].strip())
			except (IndexError, ValueError):
				pass

		return items

	def get_event_channels(self, url):
		data = self.get(url)
		item = None

		if data is None:
			return item

		try:
			root = data.xpath('//div[@id="system"]//table')[0]
			comp = root.xpath('.//td[text()="Competition"]//following-sibling::td[1]')[0]
			comp = comp.text_content().strip()
			team = root.xpath('.//td[text()="Match"]//following-sibling::td[1]')[0]
			team = team.text_content().strip().split('-')

			item = {
				'competition': comp,
				'home': team[0].strip(),
				'away': team[1].strip(),
				'channels': []
			}

			for link in data.xpath('//div[@id="system"]//a[contains(@href, "/channel/")]'):
				name = link.text_content()
				name = self.parse_name(name)
				link = link.attrib['href']

				item['channels'].append({ 'name': name, 'url': link })
		except (IndexError, ValueError):
			pass

		return item

	def get_events_streams(self):
		elink = self.get_events_link()
		links = self.get_events_links(elink)
		items = []

		for link in links:
			data = self.get_event_channels(link)

			if data is None:
				continue

			item = {
				'competition': data['competition'],
				'home': data['home'],
				'away': data['away'],
				'streams': []
			}

			for channel in data['channels']:
				streams = self.get_host_streams(channel['url'])

				for stream in streams:
					stream = self.data.get_stream({ 'url': stream['url'] })

					if stream is None:
						continue

					item['streams'].append(stream.id)

			if len(item['streams']) > 1:
				items.append(item)

		return items

	def get_fixture_match(self, fixture):
		match = None
		items = []

		for event in self.get_events_streams():
			comp_ratio = fuzz.ratio(fixture.competition.name, event['competition'])
			home_ratio = fuzz.ratio(fixture.home_team.name, event['home'])
			away_ratio = fuzz.ratio(fixture.away_team.name, event['away'])
			comb_ratio = (comp_ratio + home_ratio + away_ratio) / 3

			items.append({ 'ratio': comb_ratio, 'event': event })

		if len(items) > 0:
			sort = sorted(items, key=itemgetter('ratio'), reverse=True)[0]

			if sort['ratio'] > 70:
				match = sort['event']

		return match

	def save_channels(self):
		links = self.get_host_links()
		items = []

		for link in links:
			channels = self.get_host_channels(link['url'])

			for channel in channels:
				items.append({
					'name': channel['name'],
					'language': channel['language']
				})

		if len(items) > 0:
			self.data.set_multiple('channel', items, 'name')

	def save_streams(self):
		links = self.get_host_links()
		items = []

		for link in links:
			channels = self.get_host_channels(link['url'])

			for channel in channels:
				streams = self.get_host_streams(channel['url'])
				channel = self.data.get_channel({ 'name': channel['name'] })

				if channel is None:
					continue

				for stream in streams:
					items.append({
						'channel': channel.id,
						'host': stream['host'],
						'rate': stream['rate'],
						'url': stream['url'],
						'hd_url': stream['hd_url'],
						'language': stream['lang']
					})

		if len(items) > 0:
			self.data.set_multiple('stream', items, 'url')

	def save_events_channels(self):
		elink = self.get_events_link()
		links = self.get_events_links(elink)
		items = []

		for link in links:
			data = self.get_event_channels(link)

			if data is None:
				continue

			for channel in data['channels']:
				streams = self.get_host_streams(channel['url'])

				items.append({
					'name': channel['name'],
					'language': streams[0]['language']
				})

		if len(items) > 0:
			self.data.set_multiple('channel', items, 'name')

	def save_events_streams(self):
		elink = self.get_events_link()
		links = self.get_events_links(elink)
		items = []

		for link in links:
			data = self.get_event_channels(link)

			if data is None:
				continue

			for channel in data['channels']:
				streams = self.get_host_streams(channel['url'])
				channel = self.data.get_channel({ 'name': channel['name'] })

				if channel is None:
					continue

				for stream in streams:
					items.append({
						'channel': channel.id,
						'host': stream['host'],
						'rate': stream['rate'],
						'url': stream['url'],
						'hd_url': stream['hd_url'],
						'language': stream['lang']
					})

		if len(items) > 0:
			self.data.set_multiple('stream', items, 'url')

	def save_events(self):
		fixts = self.data.load_fixtures(True)
		items = []

		for fixture in fixts:
			if not fixture.today:
				continue

			data = self.get_fixture_match(fixture)

			if data is None:
				continue

			for stream in data['streams']:
				items.append({
					'fs_id': str(fixture.id) + '_' + str(stream),
					'fixture': fixture.id,
					'stream': stream
				})

		if len(items) > 0:
			self.data.set_multiple('event', items, 'fs_id')
