import os
import time
import socket
import subprocess
import threading

from multiprocessing.pool import ThreadPool
from datetime import datetime, timedelta, timezone
from dateutil import parser
from psutil import Popen, process_iter, cpu_count
from requests import get
from playhouse.sqliteq import SqliteQueueDatabase


def relative_path(filepath):
  root = os.path.dirname(os.path.realpath(__file__))
  root = os.path.dirname(root)

  return os.path.join(root, filepath)


def user_data_dir():
  path = "%s/.config/kickoff-player" % os.path.expanduser('~')

  if not os.path.exists(path):
    os.makedirs(path)

  return path


def database_dir(db_name):
  db_dir = os.path.join(user_data_dir(), db_name)

  if not os.path.exists(db_dir):
    open(db_dir, 'w+')

  return db_dir


def database_connection(db_name):
  db_dir  = database_dir(db_name)
  db_conn = SqliteQueueDatabase(db_dir)

  return db_conn


def gmtime(date_format=None, round_time=False):
  date = time.gmtime()
  date = datetime(*date[:6])
  date = date if not round_time else round_datetime(date)
  date = date if date_format is None else date.strftime(date_format)

  return date


def tzone(zone_format):
  return time.strftime(zone_format)


def now(date_format=None):
  date = datetime.now()
  date = date if date_format is None else date.strftime(date_format)

  return date


def today(date_format=None):
  date = datetime.today().date()
  date = date if date_format is None else date.strftime(date_format)

  return date


def yesterday(date_format=None):
  date = datetime.today() - timedelta(days=1)
  date = date if date_format is None else date.strftime(date_format)

  return date


def format_date(date, localize=False, date_format='%Y-%m-%d %H:%M:%S.%f'):
  date = parse_date(date, localize)
  date = datetime.strftime(date, date_format)

  return date


def parse_date(date, localize=False):
  date = date if not isinstance(date, str) else parser.parse(date)
  date = date if not localize else date.replace(tzinfo=timezone.utc).astimezone(tz=None)

  return date


def round_datetime(date, round_to=10):
  secs = (date - date.min).seconds
  rndg = (secs + round_to / 2 ) // round_to * round_to
  date = date + timedelta(0, rndg - secs, - date.microsecond)

  return date


def query_date_range(kwargs, date=datetime.now()):
  min_d = date - timedelta(hours=3)
  max_d = date + timedelta(**kwargs)
  dates = [min_d, max_d]

  return dates


def batch(iterable, size=1, delimiter=None):
  length = len(iterable)
  result = []

  for ndx in range(0, length, size):
    subset = iterable[ndx:min(ndx + size, length)]
    subset = subset if delimiter is None else delimiter.join(subset)

    result.append(subset)

  return result


def in_thread(**kwargs):
  thread = threading.Thread(**kwargs)
  thread.start()


def thread_pool(callback, args, flatten=True):
  pool = ThreadPool(processes=cpu_count())
  data = pool.map(callback, args)

  pool.close()
  pool.join()

  if flatten:
    data = flatten_list(data)

  return data


def run_command(args, **kwargs):
  kwargs  = merge_dicts({ 'stdout': subprocess.PIPE }, kwargs)
  command = Popen(args, **kwargs)

  return command


def active_processes():
  return process_iter()


def kill_proccess(name):
  for process in active_processes():
    if name in process.name():
      process.kill()


def flatten_list(iterable):
  if iterable and isinstance(iterable[0], list):
    iterable = [item for sublist in iterable for item in sublist]

  if iterable is None:
    iterable = []

  return iterable


def merge_dicts(first, second):
  merged = first.copy()
  merged.update(second)

  return merged


def merge_dict_keys(iterable, key_name):
  if iterable and isinstance(iterable, list):
    iterable = [item[key_name] for item in iterable if item is not None]
    iterable = flatten_list(iterable)

  if iterable is None:
    iterable = []

  return iterable


def search_dict_key(iterable, keys, default=None):
  try:
    keys = keys if isinstance(keys, list) else [keys]

    for key in keys:
      iterable = iterable[key]
  except(KeyError, TypeError):
    iterable = default

  return iterable


def replace_all(string, find, replace):
  for item in list(find):
    string = string.replace(item, replace)

  return string


def cached_request(url, cache, params=None, callback=None, **kwargs):
  url       = parse_url(url, kwargs.get('base_url'))
  cache_key = cache_key_from_url(url, params, kwargs.get('cache_key'))
  response  = cache.load(cache_key)

  if response is None:
    try:
      response = get(url, params=params)

      if response.status_code != 200:
        return None

      response = response.text if callback is None else callback(response.text)
      response = cache.save(cache_key, response, kwargs.get('ttl', 300))
    except socket.error:
      return None

  response = response.json if kwargs.get('json') else response.text
  return response


def cache_key_from_url(url, params=None, cache_key=None):
  key = url.split('://')[1]

  if cache_key is not None:
    key = "%s:%s" % (key, search_dict_key(params, cache_key))

  key = replace_all(key, ['www.', '.html', '.php'], '')
  key = replace_all(key, ['/', '?', '-', '_', '.', ',', ' '], ':')
  key = key.strip('/').strip(':').lower()

  return key


def parse_url(url, base_url=None):
  part = str(url).strip().split('://')
  host = part[0] if len(part) > 1 else 'http'
  path = part[-1].strip('/')

  if base_url is not None and base_url not in path:
    url = "%s://%s/%s" % (host, base_url.split('://')[0], path)
  else:
    url = "%s://%s" % (host, path)

  return url


def download_file(url, path, stream=False):
  try:
    response = get(url, stream=stream)
    path     = os.path.normpath(path)
    folder   = os.path.dirname(path)

    if response.status_code != 200:
      return None

    if not os.path.exists(folder):
      os.makedirs(folder)

    with open(path, 'wb') as filename:
      filename.write(response.content)
  except socket.error:
    return None

  return path
