from lxml import html
from handlers.data import DataHandler
from helpers.utils import cached_request


class LivefootballApi:

	def __init__(self):
		self.data = DataHandler()

	def get(self, url='', ttl=86400):
		response = cached_request(url=url, base_url='livefootballol.me', ttl=ttl)
		response = response if response is None else html.fromstring(response)

		return response

	def get_list_links(self):
		data = self.get()
		items = []

		if data is not None:
			try:
				headerbar = data.xpath('//div[contains(@class, "headerbar")]')[0]
				acestream = headerbar.xpath('.//a//span[text()="AceStream"]//parent::a')[0].attrib['href']
				sopcast = headerbar.xpath('.//a//span[text()="Sopcast"]//parent::a')[0].attrib['href']

				items.append({ 'name': 'AceStream', 'url': acestream })
				items.append({ 'name': 'SopCast', 'url': sopcast })
			except (IndexError, ValueError):
				pass

		return items

	def get_list_channels(self, url):
		data = self.get(url)
		items = []

		if data is not None:
			for stream in data.xpath('//div[@id="system"]//article//table//tr'):
				try:
					link = stream.xpath('.//td[2]//a')[0].attrib['href']
					name = stream.xpath('.//td[2]//strong')[0].text_content()

					if 'sopcast' in name.lower():
						lang = stream.xpath('.//td[5]')[0].text_content().strip()
						name = name.replace('Sopcast', '').replace('SopCast', '').strip()
					else:
						lang = stream.xpath('.//td[4]')[0].text_content().strip()
						name = name.replace('Acestream', '').replace('AceStream', '').strip()

					lang = 'Unknown' if lang == '' else lang.title()

					items.append({ 'name': name, 'language': lang, 'url': link })
				except (IndexError, ValueError):
					pass

		return items

	def get_list_streams(self, url):
		data = self.get(url)
		items = []

		if data is not None:
			try:
				root = data.xpath('//div[@id="system"]//table')[0]
				lang = root.xpath('.//td[text()="Language"]//following-sibling::td[1]')[0].text_content().strip()
				lang = 'NAN' if lang == '' else lang[:3].upper()
				rate = root.xpath('.//td[text()="Bitrate"]//following-sibling::td[1]')[0].text_content().strip()
				rate = 0 if rate == '' else int(rate.replace('Kbps', '').strip())

				for link in root.xpath('.//a'):
					href = link.attrib['href']
					host = href.split('://')[0].strip()

					if host in ['acestream', 'sop']:
						host = 'Sopcast' if host == 'sop' else 'Acestream'
						link = href.strip()

						items.append({ 'host': host, 'rate': rate, 'language': lang, 'url': link })
			except (IndexError, ValueError):
				pass

		return items

	def save_channels(self):
		links = self.get_list_links()
		items = []

		for link in links:
			channels = self.get_list_channels(link['url'])

			for channel in channels:
				items.append({ 'name': channel['name'], 'language': channel['language'] })

		if len(items) > 0:
			self.data.set_multiple('channel', items, 'name')

	def save_streams(self):
		links = self.get_list_links()
		items = []

		for link in links:
			channels = self.get_list_channels(link['url'])

			for channel in channels:
				streams = self.get_list_streams(channel['url'])
				channel = self.data.get_channel({ 'name': channel['name'] })

				if channel is not None:
					for stream in streams:
						items.append({
							'channel': channel.id,
							'host': stream['host'],
							'rate': stream['rate'],
							'url': stream['url'],
							'language': stream['language']
						})

		if len(items) > 0:
			self.data.set_multiple('stream', items, 'url')

	def save_events(self):
		pass
