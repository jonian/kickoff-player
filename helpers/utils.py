import time
import socket
import requests
import dateutil.parser

from datetime import datetime, timedelta, timezone


def gmtime(date_format=None, round_time=False):
	date = time.gmtime()
	date = datetime(*date[:6])
	date = date if not round_time else round_datetime(date)
	date = date if date_format is None else date.strftime(date_format)

	return date


def tzone(zone_format):
	zone = time.strftime(zone_format)

	return zone


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
	date = date if type(date) is not str else dateutil.parser.parse(date)
	date = date if not localize else date.replace(tzinfo=timezone.utc).astimezone(tz=None)

	return date


def round_datetime(date, round_to=10):
	secs = (date - date.min).seconds
	rndg = (secs + round_to / 2 ) // round_to * round_to
	date = date + timedelta(0, rndg - secs, - date.microsecond)

	return date


def query_date_range(kwargs):
	now_d = datetime.now()
	min_d = now_d - timedelta(hours=3)
	max_d = now_d + timedelta(**kwargs)
	dates = [min_d, max_d]

	return dates


def batch(iterable, n=1):
	l = len(iterable)

	for ndx in range(0, l, n):
		yield iterable[ndx:min(ndx + n, l)]


def cached_request(url, cache, base_url=None, ttl=300, json=False, params=None, callback=None):
	url = parse_url(url, base_url)
	cache_key = cache_key_from_url(url)
	headers = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0' }
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


def cache_key_from_url(url):
	key = url.split('://')[1]
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


def download_file(url, path, stream=False):
	try:
		response = requests.get(url, stream=stream)

		if response.status_code != 200:
			return None

		with open(path, 'wb') as f:
			f.write(response.content)
	except socket.error:
		return None

	return path
