import time
import socket
import requests
import dateutil.parser

from datetime import datetime, timezone, timedelta
from handlers.cache import CacheHandler


class Struct:
	def __init__(self, d):
		self.__dict__ = d


def timezone_offset(minutes=True):
	offset = time.localtime().tm_gmtoff
	offset = offset if not minutes else int(offset / 60)

	return offset

def localize_datetime(date):
	date = dateutil.parser.parse(date)
	date = date.replace(tzinfo=timezone.utc).astimezone(tz=None)
	date = datetime.strftime(date, '%Y-%m-%d %H:%M:%S.%f')

	return date


def query_date_range(kwargs):
	now_d = datetime.now()
	min_d = now_d - timedelta(hours=3)
	max_d = now_d + timedelta(**kwargs)
	dates = [min_d, max_d]

	return dates


def cached_request(url, base_url=None, ttl=300, json=False, params=None, callback=None):
	url = parse_url(url, base_url)
	cache = CacheHandler()
	cache_key = cache_key_from_url(url, params)
	headers = { 'User-Agent': 'Mozilla/5.0' }
	response = cache.load(cache_key)

	if response is None:
		try:
			response = requests.get(url, headers=headers, params=params)

			if response.status_code != 200:
				return None

			response = response.text if callback is None else callback(response.text)
			response = cache.save(cache_key, response, ttl)
		except socket.error:
			return None

	if json is True:
		return response.json
	else:
		return response.text


def cache_key_from_url(url, params=None):
	key = url.split('://')[1]

	if params is not None:
		for name, value in params.items():
			key = key + ':' + name + ':' + value

	key = key.replace('www.', '')
	key = key.replace('.html', '')
	key = key.replace('.php', '')
	key = key.replace('/', ':')
	key = key.replace('?', ':')
	key = key.replace('-', ':')
	key = key.replace('_', ':')
	key = key.replace('.', ':')
	key = key.replace(' ', ':')
	key = key.strip('/')
	key = key.strip(':')
	key = key.lower()

	return key


def parse_url(url, base_url=None):
	part = url.strip().split('://')
	host = part[0] if len(part) > 1 else 'http'
	path = part[-1].strip('/')

	if base_url is not None and base_url not in path:
		url = host + '://' + base_url.split('://')[0] + '/' + path
	else:
		url = host + '://' + path

	return url
