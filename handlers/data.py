import os

from os.path import expanduser
from datetime import datetime
from helpers.utils import query_date_range
from peewee import Model, CharField, DateTimeField, IntegerField, ForeignKeyField
from playhouse.sqlite_ext import SqliteExtDatabase


db_path = expanduser('~') + '/.kickoff-player/data.db'
db_conn = SqliteExtDatabase(db_path)


class DataHandler:

	def __init__(self):
		self.path = db_path
		self.create_db()

		self.db = db_conn
		self.register_models()

	def create_db(self):
		if not os.path.exists(self.path):
			open(self.path, 'w+')

	def register_models(self):
		tables = [Competition, Team, Fixture, Channel, Stream, Event]

		self.db.connect()
		self.db.create_tables(tables, safe=True)

	def set_single(self, model, kwargs, main_key='api_id'):
		key = kwargs.get(main_key, None)

		if key is None:
			return None

		get_item = getattr(self, 'get_' + model)
		item = get_item({ main_key: key })

		if item is None:
			create_item = getattr(self, 'create_' + model)
			item = create_item(kwargs)
		else:
			update_item = getattr(self, 'update_' + model)
			update_item(item, kwargs)

		return item

	def set_multiple(self, model, items, main_key='api_id'):
		with self.db.atomic():
			for item in items:
				self.set_single(model, item, main_key)

	def load_competitions(self):
		items = Competition.select()

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

	def load_fixtures(self):
		limit = query_date_range({ 'days': 7 })
		query = (Fixture.date > limit[0]) & (Fixture.date < limit[1])
		items = Fixture.select().where(query).order_by(Fixture.date, Fixture.competition)

		return items

	def load_today_fixtures(self):
		limit = query_date_range({ 'hours': 24 })
		query = (Fixture.date > limit[0]) & (Fixture.date < limit[1])
		items = Fixture.select().where(query).order_by(Fixture.date)

		return items

	def load_live_fixtures(self):
		limit = query_date_range({ 'hours': 0 })
		query = (Fixture.date > limit[0]) & (Fixture.date < limit[1])
		items = Fixture.select().where(query).order_by(Fixture.date)

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

	def load_channel_languages(self):
		channels = Channel.select(Channel.language)
		channels = channels.distinct(Channel.language).tuples()
		language = sorted(list(set(sum(channels, ()))))

		return language

	def load_channels(self):
		channels = Channel.select().order_by(Channel.name)

		return channels

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
	caption = CharField()
	league = CharField(unique=True)
	total_teams = IntegerField(null=True)
	total_games = IntegerField(null=True)
	year = CharField(null=True)
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

	@property

	def has_fixtures(self):
		limit = query_date_range({ 'days': 7 })
		query = (Fixture.competition == self) & (Fixture.date > limit[0]) & (Fixture.date < limit[1])
		exist = Fixture.select().where(query).exists()

		if exist:
			return True

		return False


class Team(BasicModel):
	name = CharField()
	short_name = CharField()
	crest_url = CharField(null=True)
	crest_path = CharField(null=True)
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

	def competition_names(self):
		names = self.competitions.select(Competition.name).tuples()
		names = list(sum(names, ()))

		return names

	@property

	def fixtures(self):
		query = (Fixture.home_team == self) | (Fixture.away_team == self)
		fixtures = Fixture.select().where(query)

		return fixtures

	@property

	def crest(self):
		path = self.crest_path

		if path is None or not os.path.exists(path):
			path = 'images/team-emblem.svg'

		return path

	@property

	def label_name(self):
		name = self.name

		if self.short_name != 'None' and len(name) > 20:
			name = self.short_name

		return name


class Fixture(BasicModel):
	date = DateTimeField()
	minute = CharField(null=True)
	home_team = ForeignKeyField(Team, related_name='home_team')
	home_team_goals = IntegerField(null=True)
	away_team = ForeignKeyField(Team, related_name='away_team')
	away_team_goals = IntegerField(null=True)
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
		minute = str(self.minute).replace("'", '')
		minute = minute.replace('+', '').replace(' ', '')
		minute = minute.strip()

		if minute == 'HT' or minute == 'ET' or minute.isdigit():
			return True

		return False

	@property

	def today(self):
		if self.date.date() <= datetime.today().date():
			return True

		return False

	@property

	def score(self):
		if self.home_team_goals is None and self.away_team_goals is None:
			if self.date < datetime.now():
				score = '? - ?'
			else:
				score = None
		else:
			score = str(self.home_team_goals) + ' - ' + str(self.away_team_goals)

		return score

	@property

	def local_date(self):
		local = self.date.strftime("%d/%m/%Y")

		return local

	@property

	def local_time(self):
		local = self.date.strftime("%H:%M")

		return local


class Channel(BasicModel):
	name = CharField(unique=True)
	language = CharField()
	logo_url = CharField(null=True)
	logo_path = CharField(null=True)
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)

	@property

	def logo(self):
		path = self.logo_path

		if path is None or not os.path.exists(path):
			path = 'images/channel-logo.svg'

		return path

	@property

	def streams(self):
		streams = Stream.select().where(Stream.channel == self)

		return streams

	@property

	def has_streams(self):
		exist = Stream.select().where(Stream.channel == self).exists()

		if exist:
			return True

		return False


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
		image = 'images/' + str(self.host).lower() + '.svg'

		return image


class Event(BasicModel):
	fs_id = CharField(unique=True)
	fixture = ForeignKeyField(Fixture, related_name='fixture')
	stream = ForeignKeyField(Stream, related_name='stream')
	created = DateTimeField(default=datetime.now)
	updated = DateTimeField(default=datetime.now)