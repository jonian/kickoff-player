from lxml import html
from fuzzywuzzy import fuzz
from operator import itemgetter
from handlers.cache import CacheHandler
from helpers.utils import cached_request


class WikipediaApi:

	def __init__(self):
		self.cache = CacheHandler()
		self.api_url = 'https://en.wikipedia.org/w/api.php'

	def search_term(self, term):
		try:
			params = { 'action': 'opensearch', 'search': term }
			result = cached_request(url=self.api_url, cache=self.cache, ttl=604800, params=params, json=True)
			result = result[-1][0]
		except IndexError:
			result = None

		return result

	def parse_term(self, term):
		term = term.replace('.', '')
		term = term.replace(' II', '')

		return term

	def term_variations(self, term):
		variations = [term]
		acronyms = self.term_acronyms()
		parsed = self.parse_term(term)

		for acronym in acronyms:
			if acronym.lower() not in parsed.lower():
				variations.append(parsed + ' ' + acronym)
				variations.append(acronym + ' ' + parsed)
			else:
				parsed = parsed.replace(acronym, '').strip()
				variations.append(parsed + ' ' + acronym)
				variations.append(acronym + ' ' + parsed)

		variations = list(set(variations))

		return variations

	def term_acronyms(self):
		acronyms = ['FC', 'AFC', 'CF', 'AC', 'SV', 'PSV', 'RC', 'SC']

		return acronyms

	def get_page_content(self, url):
		if url is not None:
			result = cached_request(url=url, cache=self.cache, ttl=604800)
		else:
			result = None

		return result

	def get_page_image(self, content):
		document = html.fromstring(content)
		validate = document.xpath('//table[contains(@class, "infobox")]//th[text()="League"]')

		if len(validate) > 0:
			image = document.xpath('//table[contains(@class, "infobox")]//tr[1]//a//img')

			if len(image) > 0:
				result = image[0].attrib['src']
			else:
				result = None
		else:
			result = None

		return result

	def get_page_title(self, content):
		document = html.fromstring(content)
		validate = document.xpath('//table[contains(@class, "infobox")]//th[text()="League"]')

		if len(validate) > 0:
			title = document.xpath('//h1[@id="firstHeading"]')

			if len(title) > 0:
				result = title[0].text_content().strip()
			else:
				result = None
		else:
			result = None

		return result

	def get_page_caption(self, content):
		document = html.fromstring(content)
		validate = document.xpath('//table[contains(@class, "infobox")]//th[text()="League"]')

		if len(validate) > 0:
			caption = document.xpath('//table[contains(@class, "infobox")]//caption[1]')

			if len(caption) > 0:
				result = caption[0].text_content().strip()
			else:
				result = None
		else:
			result = None

		return result

	def get_page_league(self, content):
		document = html.fromstring(content)
		validate = document.xpath('//table[contains(@class, "infobox")]//th[text()="League"]')

		if len(validate) > 0:
			league = document.xpath('//table[contains(@class, "infobox")]//th[text()="League"]//following-sibling::td[1]')

			if len(league) > 0:
				result = league[0].text_content().strip()
			else:
				result = None
		else:
			result = None

		return result

	def get_term_image(self, term, categories, strict=True):
		results = []
		ideal_ratio = 90
		min_ratio = 75

		for item in self.term_variations(term):
			url = self.search_term(item)
			txt = self.get_page_content(url)

			if not txt is None:
				image = self.get_page_image(txt)
				title = self.get_page_title(txt)
				ratio = fuzz.ratio(title, item)

				if ratio < min_ratio:
					caption = self.get_page_caption(txt)
					ratio = fuzz.ratio(caption, item)

				if strict and len(categories) > 0:
					league = self.get_page_league(txt)
					ratio = (self.calculate_list_ratio(league, categories) + ratio) / 2

				if not image is None:
					if ratio > ideal_ratio:
						return 'http:' + image
					elif ratio > min_ratio:
						results.append({ 'image': image, 'ratio': ratio })

		if len(results) > 0:
			sort = sorted(results, key=itemgetter('ratio'), reverse=True)[0]
			return 'http:' + sort['image']

		return None

	def calculate_list_ratio(self, match, items):
		results = []

		for item in items:
			ratio = fuzz.ratio(match, item)
			results.append(ratio)

		sort = sorted(results, reverse=True)[0]

		return sort
