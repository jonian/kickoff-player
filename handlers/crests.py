import os
import requests

from os.path import expanduser
from apis.wikipedia import WikipediaApi
from handlers.data import DataHandler


class CrestHandler:

	def __init__(self):
		self.data = DataHandler()

		self.img_path = expanduser('~') + '/.kickoff-player/images/'
		self.create_images_folder()

	def create_images_folder(self):
		if not os.path.exists(self.img_path):
			os.makedirs(self.img_path)

	def load_all_crests(self):
		items = []

		for team in self.data.load_teams():
			crest = self.get_team_crest(team)
			items.append({
				'api_id': team.api_id,
				'crest_url': crest[0],
				'crest_path': crest[1]
			})

		self.data.set_multiple('team', items)

	def get_team_crest(self, team):
		url = team.crest_url
		path = self.crest_filename(team.name)

		if url is None:
			url = self.get_crest_from_wikipedia(team)

		if not os.path.exists(path):
			path = self.save_image(url, team.name)

		return [url, path]

	def get_crest_from_wikipedia(self, team):
		wiki = WikipediaApi()
		image = wiki.get_term_image(team.name, team.competition_names)

		return image

	def save_image(self, url, name):
		if url is None or url == '':
			return None

		filename = self.crest_filename(name)

		if os.path.exists(filename):
			return filename

		try:
			response = requests.get(url)
			mimetype = str(url).split('.')[-1]

			if response.status_code == 200:
				tmp = self.tmp_file(filename, mimetype)

				with open(tmp, 'wb') as f:
					f.write(response.content)

				self.convert_image(filename, mimetype)
			else:
				filename = None
		except Exception:
			return None

		return filename

	def tmp_file(self, filename, mimetype):
		tmp = filename + '.' + 'tmp' + '.' + mimetype

		return tmp

	def convert_image(self, filename, mimetype):
		tmp = self.tmp_file(filename, mimetype)
		cmd = 'convert -background none -resize 128x128 "' + tmp + '" "' + filename + '"'

		os.system(cmd)
		os.remove(tmp)

	def crest_filename(self, name):
		name = name.replace(' ', '_')
		name = name.replace('/', '_')
		path = self.img_path + name + '.png'

		return path
