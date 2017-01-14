import os

from helpers.utils import format_date, gmtime, tzone, today
from helpers.utils import cached_request, download_file, batch, search_dict_key, thread_pool


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

  def get(self, url, base_url, params=None, ttl=3600, key=None, cache_key=None):
    reparams = {
      'url': url,
      'cache': self.cache,
      'base_url': base_url,
      'json': True,
      'ttl': ttl,
      'params': params,
      'cache_key': cache_key
    }

    response = cached_request(**reparams)
    response = response if response is not None else {}
    response = response if key is None else search_dict_key(response, key, [])

    return response

  def get_sections(self):
    response = self.get(url='en.json', base_url=self.sconf_url, key='sections')

    return response

  def get_competitions(self):
    response = self.get(url='en.json', base_url=self.sconf_url, key='competitions')

    return response

  def save_competitions(self):
    codes = self.get_sections()
    comps = self.get_competitions()
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
      except KeyError:
        pass

    self.data.set_multiple('competition', items, 'api_id')

  def get_competition_teams(self, competition):
    competid = str(competition.api_id)
    seasonid = str(competition.season_id)
    resource = '/'.join([competid, seasonid, 'teamsOverview.json'])
    response = self.get(url=resource, base_url=self.feedm_url, key='teams')

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
      except KeyError:
        pass

    self.data.set_multiple('team', items, 'api_id')

  def get_matchdays(self, comp_ids=None):
    reparams = {
      'url': 'en/search/matchdays',
      'base_url': self.score_url,
      'params': {
        'competitions': comp_ids,
        'since': today('%Y-%m-%d'),
        'utc_offset': tzone('%z')
      },
      'ttl': 60,
      'key': ['data', 'matchdays'],
      'cache_key': 'competitions'
    }

    response = self.get(**reparams)
    combined = []

    for item in response:
      for group in item['groups']:
        combined = combined + group['matches']

    return combined

  def get_matches(self):
    settings = self.data.get_setting({ 'key': 'competitions' })
    comp_ids = settings.value.split(',')
    comp_ids = batch(comp_ids, 5, ',')
    combined = thread_pool(self.get_matchdays, comp_ids)

    return combined

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
      except (AttributeError, KeyError):
        pass

    self.data.set_multiple('fixture', items, 'api_id')

  def get_live(self):
    reparams = {
      'url': 'matches/updates',
      'base_url': self.score_url,
      'params': {
        'since': gmtime('%Y-%m-%dT%H:%M:%SZ', True)
      },
      'ttl': 10,
      'key': ['data', 'match_updates']
    }

    response = self.get(**reparams)

    return response

  def save_live(self):
    lives = self.get_live()
    items = []

    for item in lives:
      try:
        items.append({
          'minute': item['minute'],
          'period': item['period'],
          'score_home': item['score_home'],
          'score_away': item['score_away'],
          'api_id': item['id']
        })
      except KeyError:
        pass

    self.data.set_multiple('fixture', items, 'api_id', True)

  def save_crests(self):
    teams = self.data.load_teams()

    for team in teams:
      self.download_team_crest(team)

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
