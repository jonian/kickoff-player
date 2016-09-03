import os
import time

from datetime import date
from handlers.data import DataHandler
from helpers.utils import cached_request, download_file


class FifacomApi:

	def __init__(self):
		self.data = DataHandler()

		self.api_url = 'data.fifa.com'
		self.img_url = 'img.fifa.com'

		self.country_code = str(self.get_geo_code())
		self.timez_offset = str(time.altzone / 60)
		self.current_year = date.today().year

		self.img_path = os.path.expanduser('~') + '/.kickoff-player/images/'
		self.create_images_folder()

	def get(self, url, json=True, ttl=3600):
		response = cached_request(url=url, base_url=self.api_url, callback=self.cleanup_response, json=json, ttl=ttl)
		response = response if response is not None else {}

		return response

	def get_competitions(self):
		resource = self.build_resource_url('competitions')
		response = self.get(resource)
		response = [] if response is None else response['competitions']

		return response

	def save_competitions(self):
		comps = self.get_competitions()
		items = []

		for item in comps:
			if int(item['edition']) >= self.current_year:
				items.append({
					'name': item['cupName'],
					'caption': self.get_cup_webname(item),
					'cup_id': item['idCup'],
					'edition': item['edition'],
					'country_code': self.get_country_code(item, comps),
					'country_name': self.get_country_name(item, comps)
				})

		self.data.set_multiple('competition', items, 'cup_id')

	def get_teams(self):
		resource = self.build_resource_url('teams')
		response = self.get(resource)
		response = [] if response is None else response['teams']

		return response

	def save_teams(self):
		teams = self.get_teams()
		items = []

		for item in teams:
			items.append({
				'name': item['webName'],
				'team_type': item['type'],
				'team_id': item['idTeam'],
				'country_code': self.get_country_code(item, teams),
				'country_name': self.get_country_name(item, teams),
				'crest_url': self.crest_url(item),
				'crest_path': self.crest_path(item)
			})

		self.data.set_multiple('team', items, 'team_id')

	def get_matches(self):
		resource = self.build_resource_url('matches')
		response = self.get(resource)
		response = {} if response is None else response['competitionslist']
		combined = []

		for _key, competition in response.items():
			combined = combined + competition['matchlist']

		return combined

	def save_matches(self):
		matches = self.get_matches()
		items = []

		for item in matches:
			items.append({ 'kind': item['cupKindID'], 'name': item['cupKindName'] })

		# self.data.set_multiple('fixture', items, 'api_id')

		print(list({v['kind']:v for v in items}.values()))

	def get_live(self):
		resource = self.build_resource_url('live')
		response = self.get(resource, ttl=300)
		response = {} if response is None else response
		combined = []

		for _key, competition in response.items():
			combined = combined + competition['matchlist']

		return combined

	def save_live(self):
		matches = self.get_live()
		items = []

		# for item in matches:
		# 	pass

		# self.data.set_multiple('fixture', items, 'api_id')

		print(matches)

	def save_crests(self):
		teams = self.data.load_teams()

		for team in teams:
			self.download_team_crest(team)

	def save_all_data(self):
		self.save_competitions()
		self.save_teams()
		self.save_matches()
		self.save_crests()

	def cleanup_response(self, data):
		data = data.split('(', 1)[1]
		data = data.strip(');')

		return data

	def get_geo_code(self):
		data = self.get('_esi_geo.svc', json=False)
		data = data.split('country_code:')[1]
		data = data.split('"')[1].split('"')[0]

		return data

	def build_resource_url(self, resource):
		base = 'livescores'
		lang = 'en'
		offset = self.timez_offset
		country = self.country_code

		if resource in ['competitions', 'teams']:
			parts = [base, lang, resource]

		if resource in ['matches']:
			parts = [base, lang, resource, 'bydate', 'today', offset, country]

		if resource in ['live']:
			parts = [base, resource, 'matches']

		url = '/'.join(parts)

		return url

	def get_country_name(self, item, items):
		name = item['countryName']

		if name is None:
			code = item['countryCode']
			name = list(filter(lambda ccode: ccode['countryCode'] == code, items))
			name = name[0]['countryName']
			name = name if name is not None else 'Unknown'

		return name

	def get_country_code(self, item, items):
		code = item['countryCode']

		if code is None:
			name = item['countryName']
			code = list(filter(lambda ccode: ccode['countryName'] == name, items))
			code = code[0]['countryCode']
			code = code if code is not None else 'NAN'

		return code

	def get_cup_webname(self, comp):
		name = comp['cupWebName']
		name = name if not 'fifa.' in name else comp['cupName']

		return name

	def get_team_logo(self, team, size=4):
		base = self.img_url
		size = str(size)
		team_id = str(team['idTeam'])
		image = team_id + 'x' + size + '.png'
		parts = [base, 'mm', 'teams', team_id, image]
		url = 'http://' + '/'.join(parts)

		return url

	def get_team_flag(self, team, size=4):
		base = self.img_url
		size = str(size)
		team_name = str(team['countryCode'])
		image = team_name.lower() + '.png'
		parts = [base, 'images', 'flags', size, image]
		url = 'http://' + '/'.join(parts)

		return url

	def crest_url(self, team, size=4):
		url = None

		if team['type'] == 'club':
			url = self.get_team_logo(team, size)

		if team['type'] == 'nationalteam':
			url = self.get_team_flag(team, size)

		return url

	def crest_path(self, team):
		url = self.crest_url(team)
		path = self.img_path + str(url).split('/')[-1]

		return path

	def create_images_folder(self):
		if not os.path.exists(self.img_path):
			os.makedirs(self.img_path)

	def download_team_crest(self, team):
		url = team.crest_url
		path = team.crest_path

		if not os.path.exists(path):
			path = download_file(url, path)

		return path
