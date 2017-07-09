import json

from playhouse.sqlite_ext import CharField, DateTimeField, IntegerField

from peewee import IntegrityError, Model
from helpers.utils import database_connection
from helpers.utils import now


class CacheHandler(object):

  def __init__(self):
    self.dbs = database_connection('cache.db')
    self.register_models()

  def register_models(self):
    self.dbs.connect()
    self.dbs.create_tables([Cacheable], safe=True)

  def get(self, key):
    try:
      item = Cacheable.get(key=key)
    except Cacheable.DoesNotExist:
      item = None

    return item

  def create(self, key, value, ttl=0):
    try:
      item = Cacheable.create(key=key, value=value.strip(), ttl=ttl)
    except IntegrityError:
      item = None

    return item

  def update(self, item, value, ttl=0):
    kwargs = {
      'value':   value.strip(),
      'ttl':     ttl,
      'updated': now()
    }

    try:
      query = Cacheable.update(**kwargs).where(Cacheable.key == item.key)
      query.execute()
    except IntegrityError:
      pass

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
  key     = CharField(unique=True)
  value   = CharField()
  ttl     = IntegerField(default=0)
  created = DateTimeField(default=now())
  updated = DateTimeField(default=now())

  class Meta:
    database = database_connection('cache.db')

  @property

  def text(self):
    return '' if self.value is None else str(self.value)

  @property

  def json(self):
    data = '[]' if self.value is None else str(self.value)
    data = json.loads(data)

    return data
