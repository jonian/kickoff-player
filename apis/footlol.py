import requests

from lxml import html
from handlers.data import DataHandler
from handlers.cache import CacheHandler


class FootlolApi:

	def __init__(self):
		self.cache = CacheHandler()
		self.data = DataHandler()

		self.headers = { 'User-Agent': 'Mozilla/5.0' }
		self.base_url = 'http://www.livefootballol.me'

	def cache_key(self, url):
		if not url:
			url = 'home'

		key = url.replace(self.base_url + '/', '')
		key = key.strip('/').strip('-')
		key = 'FootballLol:' + key

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

	def get_list_links(self):
		data = self.get()
		items = []

		headerbar = data.xpath('//div[contains(@class, "headerbar")]')[0]
		acestream = headerbar.xpath('.//a//span[text()="AceStream"]//parent::a')[0].attrib['href'][1:].strip()
		sopcast = headerbar.xpath('.//a//span[text()="Sopcast"]//parent::a')[0].attrib['href'][1:].strip()

		items.append({ 'name': 'AceStream', 'url': acestream })
		items.append({ 'name': 'Sopcast', 'url': sopcast })

		return items

	def get_list_streams(self, args):
		data = self.get(args['url'])
		items = []

		for stream in data.xpath('//div[@id="system"]//article//table//tr'):
			name = stream.xpath('.//td[2]//strong')[0].text_content().replace(args['name'], '').strip()
			link = stream.xpath('.//td[3]')[0].text_content().strip()
			host = args['name'].title()

			if host == 'Sopcast':
				rate = stream.xpath('.//td[4]')[0].text_content().strip()
				lang = stream.xpath('.//td[5]')[0].text_content().strip()
			else:
				lang = stream.xpath('.//td[4]')[0].text_content().strip()
				rate = stream.xpath('.//td[5]')[0].text_content().strip()

			if rate:
				rate = rate + 'Kbps'

			if link and lang and rate:
				items.append({ 'name': name, 'host': host, 'rate': rate, 'language': lang, 'url': link })

		return items

	def save_channels(self):
		items = []
		links = self.get_list_links()

		for link in links:
			streams = self.get_list_streams(link)
			items = items + streams

		self.data.set_multiple('channel', items, 'url')
