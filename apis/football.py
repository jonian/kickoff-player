import html

from handlers.data import DataHandler
from helpers.utils import localize_datetime, cached_request


class FootballApi:

	def __init__(self):
		self.data = DataHandler()

		self.api_url = 'api.football-data.org/v1'
		self.headers = {
			'X-Auth-Token': '1a4a7a5690244642917ca2e6c7b163c5',
			'X-Response-Control': 'minified'
		}

	def save_all_data(self):
		self.save_competitions()
		self.save_teams()
		self.save_fixtures(True)

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

	def extract_api_id(self, item, key='self'):
		api_id = item['_links'][key]['href'].split('/')[-1]
		api_id = int(api_id)

		return api_id

	def get(self, resource):
		response = cached_request(url=resource, base_url=self.api_url, json=True, ttl=3600)
		response = response if response is not None else {}

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
				'api_id': self.extract_api_id(item)
			})

		self.data.set_multiple('competition', items, 'api_id')

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
					'api_id': self.extract_api_id(item)
				})

		self.data.set_multiple('team', items, 'api_id')

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
			comp_api_id = self.extract_api_id(item, 'competition')
			competition = self.data.get_competition({ 'api_id': comp_api_id })

			home_api_id = self.extract_api_id(item, 'homeTeam')
			home_team = self.data.get_team({ 'api_id': home_api_id })

			away_api_id = self.extract_api_id(item, 'awayTeam')
			away_team = self.data.get_team({ 'api_id': away_api_id })

			items.append({
				'date': localize_datetime(item['date']),
				'home_team': home_team.id,
				'home_team_goals': item['result']['goalsHomeTeam'],
				'away_team': away_team.id,
				'away_team_goals': item['result']['goalsAwayTeam'],
				'competition': competition.id,
				'api_id': self.extract_api_id(item)
			})

		self.data.set_multiple('fixture', items, 'api_id')
