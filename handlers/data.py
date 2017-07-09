import os

from playhouse.sqlite_ext import CharField, IntegerField, BooleanField
from playhouse.sqlite_ext import DateTimeField, ForeignKeyField

from peewee import IntegrityError, Model
from helpers.utils import database_connection
from helpers.utils import query_date_range, parse_date, format_date, now, today


class DataHandler(object):

  def __init__(self):
    self.dbs = database_connection('data.db')
    self.register_models()

  @property

  def fx_query(self):
    first = Fixture.select().where(Fixture.date >= today()).order_by(Fixture.date).limit(1)
    odate = now() if not first else first[0].date
    limit = query_date_range({ 'days': 21 }, odate)
    query = (Fixture.date > limit[0]) & (Fixture.date < limit[1])

    return query

  @property

  def fl_query(self):
    limit = query_date_range({ 'hours': 3 })
    query = (Fixture.date > limit[0]) & (Fixture.date < limit[1])

    return query

  def register_models(self):
    tables = [Setting, Competition, Team, Fixture, Channel, Stream, Event]

    self.dbs.connect()
    self.dbs.create_tables(tables, safe=True)

  def get_model(self, model):
    try:
      model = globals()[model.title()]
    except NameError:
      return None

    return model

  def get_single(self, model, kwargs):
    model = self.get_model(model)

    try:
      item = model.get(**kwargs)
    except model.DoesNotExist:
      item = None

    return item

  def create_single(self, model, kwargs):
    model = self.get_model(model)

    try:
      item = model.create(**kwargs)
    except IntegrityError:
      item = None

    return item

  def update_single(self, model, item, kwargs):
    model = self.get_model(model)

    try:
      kwargs['updated'] = now()

      query = model.update(**kwargs).where(model.id == item.id)
      query.execute()
    except IntegrityError:
      item = None

    return item

  def set_single(self, model, kwargs, main_key='id', update=False):
    key = kwargs.get(main_key, None)

    if key is None:
      return None

    item = self.get_single(model, { main_key: key })

    if item is None and not update:
      item = self.create_single(model, kwargs)
    elif item is not None:
      item = self.update_single(model, item, kwargs)

    return item

  def set_multiple(self, model, items, main_key, update=False):
    for item in items:
      self.set_single(model, item, main_key, update)

  def load_settings(self):
    return Setting.select()

  def load_active_competitions(self, records=False):
    default = '1 4 5 7 9 17 13 19 10 18 23 33'.split(' ')
    setting = self.get_single('setting', { 'key': 'competitions' })
    setting = default if setting is None else setting

    if records:
      setting = self.load_competitions(ids=setting)

    return setting

  def load_competitions(self, current=False, name_only=False, ids=None):
    items = Competition.select()
    items = items.where(Competition.api_id << self.load_active_competitions())
    items = items if not current else items.join(Fixture).where(self.fx_query)
    items = items.distinct().order_by(Competition.section_name, Competition.api_id)
    items = items if not name_only else list(sum(items.select(Competition.name).tuples(), ()))
    items = items if ids is None else items.where(Competition.api_id << ids)

    return items

  def load_teams(self):
    return Team.select()

  def load_fixtures(self, current=False, id_only=False, today_only=False):
    items = Fixture.select().distinct()
    items = items.order_by(Fixture.date, Fixture.competition)
    items = items.where(Fixture.competition << self.load_active_competitions(True))
    items = items if not current else items.where(self.fx_query)
    items = items if not today_only else items.where(self.fl_query)
    items = items if not id_only else list(sum(items.select(Fixture.id).tuples(), ()))

    return items

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

  def load_matches_filters(self):
    filters = self.load_competitions(True, True)
    filters = ['All Competitions'] + filters

    return filters

  def load_channels_filters(self):
    filters = self.load_languages()
    filters = ['All Languages'] + filters

    return filters


class BasicModel(Model):

  class Meta:
    database = database_connection('data.db')

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
    return Fixture.select().where((Fixture.competition == self))


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
    return Event.select().where(Event.fixture == self)

  @property

  def live(self):
    pastp = ['PreMatch', 'FullTime', 'Postponed']
    fdate = parse_date(date=self.date, localize=False).date()
    fdate = fdate == today() and self.period not in pastp

    return fdate

  @property

  def today(self):
    fdate = parse_date(date=self.date, localize=False).date()
    fdate = fdate == today() and self.period != 'Postponed'

    return fdate

  @property

  def past(self):
    return self.period == 'FullTime'

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
    image = "images/%s.svg" % fname

    return image


class Event(BasicModel):
  fs_id   = CharField(unique=True)
  fixture = ForeignKeyField(Fixture, related_name='fixture')
  stream  = ForeignKeyField(Stream, related_name='stream')
  created = DateTimeField(default=now())
  updated = DateTimeField(default=now())
