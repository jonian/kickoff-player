import os

from datetime import datetime
from helpers.utils import query_date_range, parse_date, format_date
from peewee import Model, CharField, DateTimeField, IntegerField, BooleanField, ForeignKeyField
from playhouse.sqlite_ext import SqliteExtDatabase

db_path = os.path.expanduser('~') + '/.kickoff-player/data.db'
db_conn = SqliteExtDatabase(db_path)


class DataHandler:

	def __init__(self):
		self.path = db_path
		self.create_db()

		self.db = db_conn
		self.register_models()

		self.fx_limit = query_date_range({ 'days': 10 })
		self.fx_query = (Fixture.date > self.fx_limit[0]) & (Fixture.date < self.fx_limit[1])

	def create_db(self):
		if not os.path.exists(self.path):
			open(self.path, 'w+')

	def register_models(self):
		tables = [Competition, Team, Fixture, Channel, Stream, Event]

		self.db.connect()
		self.db.create_tables(tables, safe=True)

	def set_single(self, model, kwargs, main_key, update=False):
		key = kwargs.get(main_key, None)

		if key is None:
			return None

		get_item = getattr(self, 'get_' + model)
		item = get_item({ main_key: key })

		if item is None and not update:
			create_item = getattr(self, 'create_' + model)
			item = create_item(kwargs)
		elif item is not None:
			update_item = getattr(self, 'update_' + model)
			update_item(item, kwargs)

		return item

	def set_multiple(self, model, items, main_key, update=False):
		with self.db.atomic():
			for item in items:
				self.set_single(model, item, main_key, update)

	def load_competitions(self, current=False):
		items = Competition.select()
		items = items if not current else items.join(Fixture).where(self.fx_query)
		items = items.distinct()

		return items

	def get_competition(self, kwargs):
		try:
			item = Competition.get(**kwargs)
		except Competition.DoesNotExist:
			item = None

		return item

	def create_competition(self, kwargs):
		item = Competition.create(**kwargs)

		return item

	def update_competition(self, item, kwargs):
		kwargs['updated'] = datetime.now()
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
		item = Team.create(**kwargs)

		return item

	def update_team(self, item, kwargs):
		kwargs['updated'] = datetime.now()
		query = Team.update(**kwargs).where(Team.api_id == item.api_id)
		query.execute()

		return item

	def load_fixtures(self, current=False):
		items = Fixture.select()
		items = items if not current else items.where(self.fx_query)
		items = items.order_by(Fixture.date, Fixture.competition).distinct()

		return items

	def get_fixture(self, kwargs):
		try:
			item = Fixture.get(**kwargs)
		except Fixture.DoesNotExist:
			item = None

		return item

	def create_fixture(self, kwargs):
		item = Fixture.create(**kwargs)

		return item

	def update_fixture(self, item, kwargs):
		kwargs['updated'] = datetime.now()
		query = Fixture.update(**kwargs).where(Fixture.api_id == item.api_id)
		query.execute()

		return item

	def load_languages(self):
		items = Channel.select(Channel.language).join(Stream)
		items = items.distinct(Channel.language).tuples()
		items = sorted(list(set(sum(items, ()))))

		return items

	def load_channels(self, active=False):
		items = Channel.select()
		items = items if not active else items.join(Stream)
		items = items.order_by(Channel.name).distinct()

		return items

	def get_channel(self, kwargs):
		try:
			item = Channel.get(**kwargs)
		except Channel.DoesNotExist:
			item = None

		return item

	def create_channel(self, kwargs):
		item = Channel.create(**kwargs)

		return item

	def update_channel(self, item, kwargs):
		kwargs['updated'] = datetime.now()
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
		item = Stream.create(**kwargs)

		return item

	def update_stream(self, item, kwargs):
		kwargs['updated'] = datetime.now()
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
		item = Event.create(**kwargs)

		return item

	def update_event(self, item, kwargs):
		kwargs['updated'] = datetime.now()
		query = Event.update(**kwargs).where(Event.fs_id == item.fs_id)
		query.execute()

		return item


class BasicModel(Model):

	class Meta:
		database = db_conn


class Competition(BasicModel):
	name = CharField()
	short_name = CharField()
	section_code = CharField()
	section_name = CharField()
	season_id = IntegerField()
	api_id = IntegerField(unique=True)
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)

	@property

	def teams(self):
		fixtures = self.fixtures.select(Fixture.home_team, Fixture.away_team)
		fixtures = fixtures.distinct(Fixture.home_team).distinct(Fixture.away_team).tuples()
		team_ids = list(set(sum(fixtures, ())))
		teams = Team.select().where(Team.id << team_ids)

		return teams

	@property

	def fixtures(self):
		fixtures = Fixture.select().where((Fixture.competition == self))

		return fixtures


class Team(BasicModel):
	name = CharField()
	crest_url = CharField(null=True)
	crest_path = CharField(null=True)
	national = BooleanField()
	api_id = IntegerField(unique=True)
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)

	@property

	def competitions(self):
		fixtures = self.fixtures.select(Fixture.competition)
		fixtures = fixtures.distinct(Fixture.competition).tuples()
		comp_ids = list(sum(fixtures, ()))
		competitions = Competition.select().where(Competition.id << comp_ids)

		return competitions

	@property

	def fixtures(self):
		query = (Fixture.home_team == self) | (Fixture.away_team == self)
		fixtures = Fixture.select().where(query)

		return fixtures

	@property

	def crest(self):
		path = str(self.crest_path)
		path = path if os.path.exists(path) else 'images/team-emblem.svg'

		return path


class Fixture(BasicModel):
	date = DateTimeField()
	minute = IntegerField(null=True)
	period = CharField(null=True)
	home_team = ForeignKeyField(Team, related_name='home_team')
	away_team = ForeignKeyField(Team, related_name='away_team')
	score_home = IntegerField(null=True)
	score_away = IntegerField(null=True)
	competition = ForeignKeyField(Competition, related_name='competition')
	api_id = IntegerField(unique=True)
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)

	@property

	def events(self):
		events = Event.select().where(Event.fixture == self)

		return events

	@property

	def live(self):
		if self.period not in ['PreMatch', 'FullTime', 'Postponed']:
			return True

		return False

	@property

	def today(self):
		if parse_date(self.date).date() == datetime.today().date():
			return True

		return False

	@property

	def past(self):
		if self.period == 'FullTime':
			return True

		return False

	@property

	def score(self):
		posts = format_date(self.date, "%d/%m/%Y\nPostponed")
		times = format_date(self.date, "%H:%M")
		dates = format_date(self.date, "%d/%m/%Y\n%H:%M")
		score = str(self.score_home) + ' - ' + str(self.score_away)
		score = times if self.period == 'PreMatch' else score
		score = score if self.today or self.past else dates
		score = posts if self.period == 'Postponed' else score

		return score


class Channel(BasicModel):
	name = CharField(unique=True)
	language = CharField()
	logo_url = CharField(null=True)
	logo_path = CharField(null=True)
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)

	@property

	def logo(self):
		path = str(self.logo_path)
		path = path if os.path.exists(path) else 'images/channel-logo.svg'

		return path

	@property

	def streams(self):
		streams = Stream.select().where(Stream.channel == self)

		return streams


class Stream(BasicModel):
	host = CharField()
	rate = IntegerField()
	language = CharField()
	url = CharField(unique=True)
	channel = ForeignKeyField(Channel, related_name='channel', null=True)
	watched = DateTimeField(null=True)
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)

	@property

	def logo(self):
		fname = str(self.host).lower()
		image = 'images/' + fname + '.svg'

		return image


class Event(BasicModel):
	fs_id = CharField(unique=True)
	fixture = ForeignKeyField(Fixture, related_name='fixture')
	stream = ForeignKeyField(Stream, related_name='stream')
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)
