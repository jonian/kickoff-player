import html
import requests

from handlers.cache import CacheHandler
from handlers.data import DataHandler
from helpers.utils import localize_datetime


class FootballApi:

	def __init__(self):
		self.cache = CacheHandler()
		self.data = DataHandler()

		self.schema = 'https://'
		self.base_uri = 'api.football-data.org/v1/'
		self.headers = {
			'X-Auth-Token': '1a4a7a5690244642917ca2e6c7b163c5',
			'X-Response-Control': 'minified'
		}

	def save_all_data(self):
		self.save_competitions()
		self.save_teams()
		self.save_fixtures(True)

	def resource_cache_key(self, resource):
		key = 'FootballData:' + resource

		return key

	def parse_competition_name(self, item):
		captions = {
			'EC': 'European Cup',
			'WC': 'World Cup',
			'DFB': 'DFB Pokal'
		}

		caption = item.get('caption', '')
		year = item.get('year', '')
		league = item.get('league', '')
		default = caption.split(year)[0].strip().title()
		name = captions.get(league, default)

		return name

	def get(self, resource):
		resource = resource.split('://')[-1].replace(self.base_uri, '')
		cache_key = self.resource_cache_key(resource)

		try:
			response = self.cache.load(cache_key)

			if response is None:
				response = requests.get(self.schema + self.base_uri + resource, headers=self.headers)

				if response.status_code == 200:
					self.cache.save(cache_key, response.content, 3600)

			response = response.json()
		except Exception:
			response = {}

		return response

	def get_competitions(self):
		response = self.get('competitions')

		return response

	def save_competitions(self):
		items = []

		for item in self.get_competitions():
			items.append({
				'name': self.parse_competition_name(item),
				'caption': item['caption'],
				'league': item['league'],
				'total_teams': item['numberOfTeams'],
				'total_games': item['numberOfGames'],
				'year': item['year'],
				'api_id': item['id']
			})

		self.data.set_multiple('competition', items)

	def get_teams(self, competition_id):
		teams = self.get('competitions/' + str(competition_id) + '/teams')
		teams = teams.get('teams', [])

		return teams

	def save_teams(self):
		items = []

		for competition in self.data.load_competitions():
			for item in self.get_teams(competition.api_id):
				items.append({
					'name': html.unescape(str(item['name'])),
					'short_name': html.unescape(str(item['shortName'])),
					'crest_url': item['crestUrl'],
					'api_id': item['id']
				})

		self.data.set_multiple('team', items)

	def get_fixtures(self, competition_id=None):
		if competition_id is None:
			response = self.get('fixtures')
		else:
			response = self.get('competitions/' + str(competition_id) + '/fixtures')

		response = response.get('fixtures', [])

		return response

	def save_fixtures(self, recursive=False):
		fixtures = []
		items = []

		if recursive is False:
			fixtures = self.get_fixtures()
		else:
			for competition in self.data.load_competitions():
				data = self.get_fixtures(competition.api_id)
				fixtures = fixtures + data

		for item in fixtures:
			competition = self.data.get_competition({ 'api_id': item['competitionId'] })
			home_team = self.data.get_team({ 'api_id': item['homeTeamId'] })
			away_team = self.data.get_team({ 'api_id': item['awayTeamId'] })

			items.append({
				'date': localize_datetime(item['date']),
				'home_team': home_team.id,
				'home_team_goals': item['result']['goalsHomeTeam'],
				'away_team': away_team.id,
				'away_team_goals': item['result']['goalsAwayTeam'],
				'competition': competition.id,
				'api_id': item['id']
			})

		self.data.set_multiple('fixture', items)
