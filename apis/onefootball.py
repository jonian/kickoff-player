import os

from helpers.utils import cached_request, download_file, format_date, gmtime, tzone, today, batch


class OnefootballApi:

	def __init__(self, data, cache):
		self.data = data
		self.cache = cache

		self.score_url = 'scores-api.onefootball.com/v1'
		self.sconf_url = 'config.onefootball.com/api/scoreconfig2'
		self.feedm_url = 'feedmonster.onefootball.com/feeds/il/en/competitions'
		self.image_url = 'images.onefootball.com/icons/teams'

		self.img_path = os.path.expanduser('~') + '/.kickoff-player/images/'
		self.create_images_folder()

	def get(self, url, base_url, params=None, ttl=3600):
		response = cached_request(url=url, cache=self.cache, base_url=base_url, json=True, ttl=ttl, params=params)
		response = response if response is not None else {}

		return response

	def get_competitions(self):
		response = self.get(url='en.json', base_url=self.sconf_url)

		return response

	def save_competitions(self):
		cdata = self.get_competitions()
		comps = cdata['competitions'] if cdata is not None else []
		codes = cdata['sections'] if cdata is not None else []
		items = []

		for item in comps:
			try:
				items.append({
					'name': item['competitionName'],
					'short_name': item['competitionShortName'],
					'section_code': item['section'],
					'section_name': self.section_name(codes, item['section']),
					'season_id': item['seasonId'],
					'api_id': item['competitionId']
				})
			except IndexError:
				pass

		self.data.set_multiple('competition', items, 'api_id')

	def get_competition_teams(self, competition):
		competid = str(competition.api_id)
		seasonid = str(competition.season_id)
		resource = '/'.join([competid, seasonid, 'teamsOverview.json'])
		response = self.get(url=resource, base_url=self.feedm_url)
		response = response['teams'] if response is not None else []

		return response

	def get_teams(self):
		comps = self.data.load_competitions()
		items = []

		for competition in comps:
			items = items + self.get_competition_teams(competition)

		return items

	def save_teams(self):
		teams = self.get_teams()
		items = []

		for item in teams:
			try:
				items.append({
					'name': item['name'],
					'crest_url': self.crest_url(item),
					'crest_path': self.crest_path(item),
					'national': item['isNational'],
					'api_id': item['idInternal']
				})
			except IndexError:
				pass

		self.data.set_multiple('team', items, 'api_id')

	def get_matchdays(self, comp_ids=None):
		comp_ids = '' if comp_ids is None else ','.join(map(str, comp_ids))
		currdate = today('%Y-%m-%d')
		tzoffset = tzone('%z')
		separams = { 'competitions': comp_ids, 'since': currdate, 'utc_offset': tzoffset }
		response = self.get(url='en/search/matchdays', base_url=self.score_url, params=separams, ttl=0)
		response = response['data']['matchdays'] if response is not None else []
		combined = []

		for item in response:
			for group in item['groups']:
				combined = combined + group['matches']

		return combined

	def get_matches(self):
		comp_ids = [5, 7, 1, 2, 4, 9, 27, 17, 13, 30, 19, 10, 28, 18, 23, 29, 33, 56, 126]
		response = []

		for item in batch(comp_ids, 5):
			response = response + self.get_matchdays(item)

		return response

	def save_matches(self):
		matches = self.get_matches()
		items = []

		for item in matches:
			try:
				competition = self.data.get_competition({ 'api_id': item['competition']['id'] })
				home_team = self.data.get_team({ 'api_id': item['team_home']['id'] })
				away_team = self.data.get_team({ 'api_id': item['team_away']['id'] })
				form_date = format_date(date=item['kickoff'], localize=True)

				items.append({
					'date': form_date,
					'minute': item['minute'],
					'period': item['period'],
					'home_team': home_team.id,
					'away_team': away_team.id,
					'score_home': item['score_home'],
					'score_away': item['score_away'],
					'competition': competition.id,
					'api_id': item['id']
				})
			except (AttributeError, IndexError):
				pass

		self.data.set_multiple('fixture', items, 'api_id')

	def get_live(self):
		currdate = gmtime('%Y-%m-%dT%H:%M:%SZ', True)
		separams = { 'since': currdate }
		response = self.get(url='matches/updates', base_url=self.score_url, params=separams, ttl=9)
		response = response['data']['match_updates'] if response is not None else []

		return response

	def save_live(self):
		matches = self.get_live()
		items = []

		for item in matches:
			try:
				items.append({
					'minute': item['minute'],
					'period': item['period'],
					'score_home': item['score_home'],
					'score_away': item['score_away'],
					'api_id': item['id']
				})
			except IndexError:
				pass

		self.data.set_multiple('fixture', items, 'api_id', True)

	def save_crests(self):
		teams = self.data.load_teams()

		for team in teams:
			self.download_team_crest(team)

	def save_all_data(self):
		self.save_competitions()
		self.save_teams()
		self.save_matches()
		self.save_crests()

	def section_name(self, codes, code):
		name = list(filter(lambda ccode: ccode['key'] == code, codes))
		name = name[0]['title']

		return name

	def crest_url(self, team, size='56'):
		img = str(team['idInternal']) + '.png'
		url = 'http://' + '/'.join([self.image_url, size, img])

		return url

	def crest_path(self, team):
		link = self.crest_url(team)
		path = self.img_path + str(link).split('/')[-1]

		return path

	def create_images_folder(self):
		if not os.path.exists(self.img_path):
			os.makedirs(self.img_path)

	def download_team_crest(self, team):
		link = team.crest_url
		path = team.crest_path

		if not os.path.exists(path):
			path = download_file(link, path)

		return path
