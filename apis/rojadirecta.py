import requests

from lxml import html
from selenium import webdriver
from handlers.data import DataHandler
from handlers.cache import CacheHandler


class RojadirectaApi:

	def __init__(self):
		self.cache = CacheHandler()
		self.data = DataHandler()

		self.headers = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/21.0' }
		self.base_url = 'http://www.rojadirecta.me/en'

	def cache_key(self, url):
		if not url:
			url = 'home'

		key = url.replace(self.base_url + '/', '')
		key = key.strip('/').strip('-')
		key = 'RojaDirecta:' + key

		return key

	def get_alt(self, url=''):
		driver = webdriver.PhantomJS()
		driver.get(self.base_url + '/' + url)

		page_source = driver.page_source
		driver.quit()

		document = html.fromstring(page_source)

		return document

	def get(self, url=''):
		cache_key = self.cache_key(url)

		try:
			response = self.cache.load(cache_key)

			if response is None:
				response = requests.get(self.base_url + '/' + url, headers=self.headers, stream=True)

				if response.status_code == 200:
					self.cache.save(cache_key, response.text, 300)

			response = response.text
		except Exception:
			response = '<html><body></body></html>'

		response = html.fromstring(response)

		return response

	def get_list_links(self):
		data = self.get_alt()
		items = []

		# headerbar = data.xpath('//div[contains(@class, "headerbar")]')[0]
		# acestream = headerbar.xpath('.//a//span[text()="AceStream"]//parent::a')[0].attrib['href'][1:].strip()
		# sopcast = headerbar.xpath('.//a//span[text()="Sopcast"]//parent::a')[0].attrib['href'][1:].strip()

		for fixture in data.xpath('//div[@id="agendadiv"]//div[contains(@class, "menutitle")]'):
			date = fixture.xpath('.//meta[@itemprop="startDate"]')

			if len(date) > 0:
				date = date[0].attrib['content']
			else:
				date = None

			country = fixture.xpath('.//span[contains(@class, "en")]')

			if len(country) > 0:
				country = country = country[0].text_content().strip()
			else:
				country = None

			name = fixture.xpath('.//meta[@itemprop="name"]')

			if len(name) > 0:
				name = name[0].text_content().strip()
				home = name.split('-')[0].strip()
				away = name.split('-')[1].strip()
			else:
				home = None
				away = None

			items.append({ 'date': date, 'country': country, 'home': home, 'away': away })

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
