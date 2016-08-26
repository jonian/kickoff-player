import dateutil.parser

from datetime import datetime, timezone, timedelta


class Struct:
	def __init__(self, d):
		self.__dict__ = d


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
