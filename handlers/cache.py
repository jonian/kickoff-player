import os
import json

from peewee import Model, CharField, DateTimeField, IntegerField
from playhouse.sqlite_ext import SqliteExtDatabase
from helpers.utils import now

db_path = os.path.expanduser('~') + '/.kickoff-player/cache.db'
db_conn = SqliteExtDatabase(db_path)


class CacheHandler(object):

	def __init__(self):
		self.path = db_path
		self.create_db()

		self.db = db_conn
		self.register_models()

	def create_db(self):
		if not os.path.exists(self.path):
			open(self.path, 'w+')

	def register_models(self):
		self.db.connect()
		self.db.create_tables([Cacheable], safe=True)

	def get(self, key):
		try:
			item = Cacheable.get(key=key)
		except Cacheable.DoesNotExist:
			item = None

		return item

	def create(self, key, value, ttl=0):
		value = value.strip()
		item = Cacheable.create(key=key, value=value, ttl=ttl)

		return item

	def update(self, item, value, ttl=0):
		kwargs = {
			'value': value.strip(),
			'ttl': ttl,
			'updated': now()
		}

		query = Cacheable.update(**kwargs).where(Cacheable.key == item.key)
		query.execute()

		return item

	def load(self, key):
		item = self.get(key)

		if self.is_valid(item):
			return item

		return None

	def save(self, key, value, ttl=0):
		item = self.get(key)

		if item is None:
			item = self.create(key, value, ttl)
		else:
			item = self.update(item, value, ttl)

		return item

	def is_valid(self, item):
		try:
			diff = (now() - item.updated).total_seconds()

			if abs(diff) < abs(item.ttl):
				return True
		except AttributeError:
			pass

		return False


class Cacheable(Model):
	key = CharField(unique=True)
	value = CharField()
	ttl = IntegerField(default=0)
	created = DateTimeField(default=now())
	updated = DateTimeField(default=now())

	class Meta:
		database = db_conn

	@property

	def text(self):
		data = '' if self.value is None else str(self.value)

		return data

	@property

	def json(self):
		data = '[]' if self.value is None else str(self.value)
		data = json.loads(data)

		return data
