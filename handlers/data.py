import os

from playhouse.apsw_ext import APSWDatabase
from playhouse.apsw_ext import CharField, DateTimeField, IntegerField, BooleanField, ForeignKeyField

from peewee import IntegrityError, Model
from helpers.utils import query_date_range, parse_date, format_date, now, today

db_path = os.path.expanduser('~') + '/.kickoff-player/data.db'
db_conn = APSWDatabase(db_path)


class DataHandler(object):

  def __init__(self):
    self.path = db_path
    self.create_db()

    self.db = db_conn
    self.register_models()

    self.fx_limit = query_date_range({ 'days': 14 })
    self.fx_query = (Fixture.date > self.fx_limit[0]) & (Fixture.date < self.fx_limit[1])

    self.fl_limit = query_date_range({ 'hours': 3 })
    self.fl_query = (Fixture.date > self.fl_limit[0]) & (Fixture.date < self.fl_limit[1])

  def create_db(self):
    if not os.path.exists(self.path):
      open(self.path, 'w+')

  def register_models(self):
    tables = [Setting, Competition, Team, Fixture, Channel, Stream, Event]

    self.db.connect()
    self.db.create_tables(tables, safe=True)

  def set_single(self, model, kwargs, main_key, update=False):
    key = kwargs.get(main_key, None)

    if key is None:
      return None

    get_item = getattr(self, 'get_' + model)
    item     = get_item({ main_key: key })

    if item is None and not update:
      create_item = getattr(self, 'create_' + model)
      item        = create_item(kwargs)
    elif item is not None:
      update_item = getattr(self, 'update_' + model)
      update_item(item, kwargs)

    return item

  def set_multiple(self, model, items, main_key, update=False):
    with self.db.atomic():
      for item in items:
        self.set_single(model, item, main_key, update)

  def load_settings(self):
    items = Setting.select()

    return items

  def get_setting(self, kwargs):
    try:
      item = Setting.get(**kwargs)
    except Setting.DoesNotExist:
      item = None

    return item

  def create_setting(self, kwargs):
    try:
      item = Setting.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_setting(self, item, kwargs):
    query = Setting.update(**kwargs).where(Setting.key == item.key)
    query.execute()

    return item

  def load_competitions(self, current=False, name_only=False, ids=None):
    items = Competition.select()
    items = items if not current else items.join(Fixture).where(self.fx_query)
    items = items.distinct().order_by(Competition.section_name, Competition.api_id)
    items = items if not name_only else list(sum(items.select(Competition.name).tuples(), ()))
    items = items if ids is None else items.where(Competition.api_id << ids)

    return items

  def get_competition(self, kwargs):
    try:
      item = Competition.get(**kwargs)
    except Competition.DoesNotExist:
      item = None

    return item

  def create_competition(self, kwargs):
    try:
      item = Competition.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_competition(self, item, kwargs):
    kwargs['updated'] = now()

    query = Competition.update(**kwargs).where(Competition.api_id == item.api_id)
    query.execute()

    return item

  def load_teams(self):
    items = Team.select()

    return items

  def get_team(self, kwargs):
    try:
      item = Team.get(**kwargs)
    except Team.DoesNotExist:
      item = None

    return item

  def create_team(self, kwargs):
    try:
      item = Team.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_team(self, item, kwargs):
    kwargs['updated'] = now()
    query = Team.update(**kwargs).where(Team.api_id == item.api_id)
    query.execute()

    return item

  def load_fixtures(self, current=False, id_only=False, today_only=False):
    items = Fixture.select().distinct()
    items = items.order_by(Fixture.date, Fixture.competition)
    items = items if not current else items.where(self.fx_query)
    items = items if not today_only else items.where(self.fl_query)
    items = items if not id_only else list(sum(items.select(Fixture.id).tuples(), ()))

    return items

  def get_fixture(self, kwargs):
    try:
      item = Fixture.get(**kwargs)
    except Fixture.DoesNotExist:
      item = None

    return item

  def create_fixture(self, kwargs):
    try:
      item = Fixture.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_fixture(self, item, kwargs):
    kwargs['updated'] = now()

    query = Fixture.update(**kwargs).where(Fixture.api_id == item.api_id)
    query.execute()

    return item

  def load_languages(self):
    items = Channel.select(Channel.language).join(Stream)
    items = items.distinct(Channel.language).tuples()
    items = sorted(list(set(sum(items, ()))))

    return items

  def load_channels(self, active=False, id_only=False):
    items = Channel.select()
    items = items if not active else items.join(Stream)
    items = items.order_by(Channel.name).distinct()
    items = items if not id_only else list(sum(items.select(Channel.id).tuples(), ()))

    return items

  def get_channel(self, kwargs):
    try:
      item = Channel.get(**kwargs)
    except Channel.DoesNotExist:
      item = None

    return item

  def create_channel(self, kwargs):
    try:
      item = Channel.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_channel(self, item, kwargs):
    kwargs['updated'] = now()

    query = Channel.update(**kwargs).where(Channel.name == item.name)
    query.execute()

    return item

  def get_stream(self, kwargs):
    try:
      item = Stream.get(**kwargs)
    except Stream.DoesNotExist:
      item = None

    return item

  def create_stream(self, kwargs):
    try:
      item = Stream.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_stream(self, item, kwargs):
    kwargs['updated'] = now()

    query = Stream.update(**kwargs).where(Stream.url == item.url)
    query.execute()

    return item

  def get_event(self, kwargs):
    try:
      item = Event.get(**kwargs)
    except Event.DoesNotExist:
      item = None

    return item

  def create_event(self, kwargs):
    try:
      item = Event.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_event(self, item, kwargs):
    kwargs['updated'] = now()

    query = Event.update(**kwargs).where(Event.fs_id == item.fs_id)
    query.execute()

    return item

  def load_matches_filters(self):
    filters = self.load_competitions(True, True)
    filters = ['All Competitions'] + filters if len(filters) else filters

    return filters

  def load_channels_filters(self):
    filters = self.load_languages()
    filters = ['All Languages'] + filters if len(filters) else filters

    return filters

  def load_active_competitions(self, records=False):
    default = '1 2 5 9 17 13 19 10 18 23 33'.split(' ')
    setting = self.get_setting({ 'key': 'competitions' })
    setting = default if setting is None else setting

    if records:
      return self.load_competitions(ids=setting)
    else:
      return setting


class BasicModel(Model):

  class Meta:
    database = db_conn

  def reload(self):
    return self.get(id=self.id)


class Setting(BasicModel):
  key   = CharField(unique=True)
  value = CharField()


class Competition(BasicModel):
  name         = CharField()
  short_name   = CharField()
  section_code = CharField()
  section_name = CharField()
  season_id    = IntegerField()
  api_id       = IntegerField(unique=True)
  created      = DateTimeField(default=now())
  updated      = DateTimeField(default=now())

  @property

  def teams(self):
    fixtures = self.fixtures.select(Fixture.home_team, Fixture.away_team)
    fixtures = fixtures.distinct(Fixture.home_team).distinct(Fixture.away_team).tuples()
    team_ids = list(set(sum(fixtures, ())))
    teams    = Team.select().where(Team.id << team_ids)

    return teams

  @property

  def fixtures(self):
    fixtures = Fixture.select().where((Fixture.competition == self))

    return fixtures


class Team(BasicModel):
  name       = CharField()
  crest_url  = CharField(null=True)
  crest_path = CharField(null=True)
  national   = BooleanField()
  api_id     = IntegerField(unique=True)
  created    = DateTimeField(default=now())
  updated    = DateTimeField(default=now())

  @property

  def competitions(self):
    fixtures     = self.fixtures.select(Fixture.competition)
    fixtures     = fixtures.distinct(Fixture.competition).tuples()
    comp_ids     = list(sum(fixtures, ()))
    competitions = Competition.select().where(Competition.id << comp_ids)

    return competitions

  @property

  def fixtures(self):
    query    = (Fixture.home_team == self) | (Fixture.away_team == self)
    fixtures = Fixture.select().where(query)

    return fixtures

  @property

  def crest(self):
    path = str(self.crest_path)
    path = path if os.path.exists(path) else 'images/team-emblem.svg'

    return path


class Fixture(BasicModel):
  date        = DateTimeField()
  minute      = IntegerField(null=True)
  period      = CharField(null=True)
  home_team   = ForeignKeyField(Team, related_name='home_team')
  away_team   = ForeignKeyField(Team, related_name='away_team')
  score_home  = IntegerField(null=True)
  score_away  = IntegerField(null=True)
  competition = ForeignKeyField(Competition, related_name='competition')
  api_id      = IntegerField(unique=True)
  created     = DateTimeField(default=now())
  updated     = DateTimeField(default=now())

  @property

  def events(self):
    events = Event.select().where(Event.fixture == self)

    return events

  @property

  def live(self):
    fdate = parse_date(date=self.date, localize=False).date()

    if fdate == today() and self.period not in ['PreMatch', 'FullTime', 'Postponed']:
      return True

    return False

  @property

  def today(self):
    fdate = parse_date(date=self.date, localize=False).date()

    if fdate == today() and not self.period == 'Postponed':
      return True

    return False

  @property

  def past(self):
    if self.period == 'FullTime':
      return True

    return False

  @property

  def score(self):
    posts = format_date(date=self.date, date_format="%d/%m/%Y\nPostponed")
    times = format_date(date=self.date, date_format="%H:%M")
    dates = format_date(date=self.date, date_format="%d/%m/%Y\n%H:%M")
    score = str(self.score_home) + ' - ' + str(self.score_away)
    score = times if self.period == 'PreMatch' else score
    score = score if self.today or self.past else dates
    score = posts if self.period == 'Postponed' else score

    return score


class Channel(BasicModel):
  name      = CharField(unique=True)
  language  = CharField()
  logo_url  = CharField(null=True)
  logo_path = CharField(null=True)
  created   = DateTimeField(default=now())
  updated   = DateTimeField(default=now())

  @property

  def logo(self):
    path = str(self.logo_path)
    path = path if os.path.exists(path) else 'images/channel-logo.svg'

    return path

  @property

  def streams(self):
    streams = Stream.select().where(Stream.channel == self).limit(2)
    streams = streams.distinct(Stream.host).order_by(Stream.created)

    return streams


class Stream(BasicModel):
  host     = CharField()
  rate     = IntegerField()
  language = CharField()
  url      = CharField(unique=True)
  hd_url   = CharField(null=True)
  channel  = ForeignKeyField(Channel, related_name='channel', null=True)
  watched  = DateTimeField(null=True)
  created  = DateTimeField(default=now())
  updated  = DateTimeField(default=now())

  @property

  def logo(self):
    fname = str(self.host).lower()
    image = 'images/' + fname + '.svg'

    return image


class Event(BasicModel):
  fs_id   = CharField(unique=True)
  fixture = ForeignKeyField(Fixture, related_name='fixture')
  stream  = ForeignKeyField(Stream, related_name='stream')
  created = DateTimeField(default=now())
  updated = DateTimeField(default=now())
