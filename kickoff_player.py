#! /usr/bin/python3

import gi
import signal

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from handlers.events import EventHandler
from handlers.data import DataHandler
from handlers.stream import StreamHandler
from handlers.player import PlayerHandler
from helpers.utils import Struct

GObject.threads_init()

class KickoffPlayer:

	def __init__(self):
		self.data = DataHandler()
		self.add_extra_styles('ui/styles.css')

		self.builder = Gtk.Builder()
		self.builder.add_from_file('ui/player.ui')

		self.window = self.builder.get_object('window_main')
		self.window.show_all()

		self.player = PlayerHandler(self)
		self.stream = StreamHandler(self)

		self.events = EventHandler(self)
		self.builder.connect_signals(self.events)

		GObject.idle_add(self.add_events_filters)
		GObject.idle_add(self.add_events_list)

		GObject.idle_add(self.add_channels_filters)
		GObject.idle_add(self.add_channels_list)

	def run(self):
		Gtk.main()

	def quit(self):
		Gtk.main_quit()

	def widget_add_class(self, widget, classes):
		context = widget.get_style_context()

		if type(classes) not in (tuple, list):
			classes = classes.split(' ')

		for name in classes:
			context.add_class(name)

	def widget_remove_children(self, widget):
		children = widget.get_children()

		for child in children:
			widget.remove(child)

	def image_from_path(self, path, size=48, fallback='images/team-emblem.svg'):
		image = Gtk.Image(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)

		try:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
		except Exception:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fallback, size, size, True)

		image.set_from_pixbuf(pixbuf)

		return image

	def add_extra_styles(self, path):
		path_style_provider = Gtk.CssProvider()
		path_style_provider.load_from_path(path)

		Gtk.StyleContext.add_provider_for_screen(
			Gdk.Screen.get_default(),
			path_style_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)

	def add_events_filters(self):
		default = Struct({ 'id': 'all', 'league': 'ALL', 'name': 'All Competitions' })
		self.add_events_filters_item(default, 0)

		position = 0
		competitions = self.data.load_competitions()

		for competition in competitions:
			if competition.has_fixtures:
				position = position + 1
				self.add_events_filters_item(competition, position)

	def add_events_filters_item(self, data, position):
		label_args = {
			'justify': Gtk.Justification.LEFT,
			'halign': Gtk.Align.START,
			'margin_top': 10,
			'margin_bottom': 10,
			'margin_left': 10,
			'margin_right': 10
		}

		label = Gtk.Label(data.name, **label_args)
		item = Gtk.ListBoxRow(name='comp-' + str(data.id))
		item.add(label)
		item.show_all()

		listbox = self.builder.get_object('list_box_events_filters')
		listbox.insert(item, position)

	def add_events_list(self):
		position = 0
		fixtures = self.data.load_fixtures()

		for fixture in fixtures:
			position = position + 1
			self.add_events_list_item(fixture, position)

	def add_events_list_item(self, data, position):
		teams = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True)
		self.add_event_teams(teams, data)

		streams = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		self.widget_add_class(streams, 'event-item-streams')

		count = data.events.count()
		label = Gtk.Label(str(count), margin_right=10)
		streams.pack_start(label, False, False, 0)
		self.widget_add_class(label, 'event-item-counter')

		if count == 0:
			self.widget_add_class(label, 'no-streams')

		label = Gtk.Label('Streams available', halign=Gtk.Align.START)
		streams.pack_start(label, False, False, 0)

		button = Gtk.Button.new_from_icon_name(icon_name='media-playback-start-symbolic', size=Gtk.IconSize.BUTTON)
		streams.pack_end(button, False, False, 1)
		self.widget_add_class(button, 'event-item-details')
		button.connect('clicked', self.events.on_event_details_button_clicked, data)

		if count == 0:
			button.set_sensitive(False)
			button.set_opacity(0)

		outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		outer.pack_start(teams, True, True, 0)
		outer.pack_start(streams, True, True, 1)

		child = Gtk.FlowBoxChild(name='comp-' + str(data.competition_id), valign=Gtk.Align.START)
		self.widget_add_class(child, 'event-item')

		child.add(outer)
		child.show_all()

		flowbox = self.builder.get_object('flow_box_events_list')
		flowbox.insert(child, position)

	def add_event_teams(self, box, data):
		box_args = {
			'orientation': Gtk.Orientation.VERTICAL,
			'spacing': 10,
			'margin_top': 10,
			'margin_bottom': 10,
			'margin_left': 10,
			'margin_right': 10
		}

		home = Gtk.Box(**box_args)
		image = self.image_from_path(data.home_team.crest)
		label = Gtk.Label(data.home_team.label_name)
		self.widget_add_class(image, 'team-emblem')
		self.widget_add_class(label, 'team-name')
		home.pack_start(image, True, True, 0)
		home.pack_start(label, True, True, 1)

		away = Gtk.Box(**box_args)
		image = self.image_from_path(data.away_team.crest)
		label = Gtk.Label(data.away_team.label_name)
		self.widget_add_class(image, 'team-emblem')
		self.widget_add_class(label, 'team-name')
		away.pack_start(image, True, True, 0)
		away.pack_start(label, True, True, 1)

		label_args = {
			'justify': Gtk.Justification.CENTER,
			'halign': Gtk.Align.CENTER,
			'valign': Gtk.Align.CENTER
		}

		if data.score is None:
			if data.today:
				date = data.local_time
				label = Gtk.Label(date, **label_args)
				self.widget_add_class(label, 'event-today')
			else:
				date = data.local_date + '\n' + data.local_time
				label = Gtk.Label(date, **label_args)
				self.widget_add_class(label, 'event-date')
		else:
			label = Gtk.Label(data.score, **label_args)
			self.widget_add_class(label, 'event-score')

			if data.live:
				self.widget_add_class(label, 'event-live')

		score = Gtk.Box(**box_args)
		score.pack_start(label, True, True, 0)

		box.pack_start(home, True, True, 0)
		box.pack_start(score, True, True, 1)
		box.pack_start(away, True, True, 2)

		box.show_all()

	def add_event_streams(self, listbox, events):
		position = 0

		for event in events:
			position = position + 1
			self.add_event_stream_item(listbox, event, position)

	def add_event_stream_item(self, listbox, event, position):
		row = Gtk.ListBoxRow()
		listbox.insert(row, position)
		self.widget_add_class(row, 'stream-item')

		item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		row.add(item)

		label = Gtk.Label(event.stream.language, halign=Gtk.Align.START, margin_right=10)
		item.pack_start(label, False, False, 0)
		self.widget_add_class(label, 'stream-language')

		image = self.image_from_path(event.stream.logo, 16)
		image.set_halign(Gtk.Align.START)
		item.pack_start(image, False, False, 1)
		self.widget_add_class(image, 'stream-image')

		if event.stream.channel is None:
			label = Gtk.Label('Unknown Channel', halign=Gtk.Align.START, margin_left=10)
			self.widget_add_class(label, 'stream-unknown')
		else:
			label = Gtk.Label(event.stream.channel.name, halign=Gtk.Align.START, margin_left=10)
			self.widget_add_class(label, 'stream-name')

		item.pack_start(label, False, False, 2)

		label = Gtk.Label(str(event.stream.rate) + 'Kbps', halign=Gtk.Align.END, margin_right=10)
		item.pack_start(label, True, True, 3)
		self.widget_add_class(label, 'stream-rate')

		button = Gtk.Button.new_from_icon_name(icon_name='media-playback-start-symbolic', size=Gtk.IconSize.BUTTON)
		item.pack_start(button, False, False, 4)
		self.widget_add_class(button, 'stream-play')
		button.connect('clicked', self.events.on_stream_play_button_clicked, event.stream.url)

		row.show_all()

	def add_channels_filters(self):
		position = 0
		languages = self.data.load_channel_languages()
		languages = ['All Languages'] + languages

		for language in languages:
			position = position + 1
			self.add_channels_filters_item(language, position)

	def add_channels_filters_item(self, data, position):
		lang_id = str(data).split()[0].lower()
		lang_nm = str(data).title()

		label_args = {
			'justify': Gtk.Justification.LEFT,
			'halign': Gtk.Align.START,
			'margin_top': 10,
			'margin_bottom': 10,
			'margin_left': 10,
			'margin_right': 10
		}

		label = Gtk.Label(lang_nm, **label_args)
		item = Gtk.ListBoxRow(name='lang-' + lang_id)
		item.add(label)
		item.show_all()

		listbox = self.builder.get_object('list_box_channels_filters')
		listbox.insert(item, position)

	def add_channels_list(self):
		position = 0
		channels = self.data.load_channels()

		for channel in channels:
			if channel.has_streams:
				position = position + 1
				self.add_channels_list_item(channel, position)

	def add_channels_list_item(self, data, position):
		lang_id = data.language.split()[0].lower()

		box_args = {
			'orientation': Gtk.Orientation.VERTICAL,
			'margin_top': 10,
			'margin_bottom': 10,
			'margin_left': 10,
			'margin_right': 10,
			'spacing': 10
		}

		name = Gtk.Box(**box_args)

		image = self.image_from_path(data.logo)
		name.pack_start(image, False, False, 0)

		label = Gtk.Label(data.name, halign=Gtk.Align.CENTER)
		name.pack_start(label, True, True, 0)
		self.widget_add_class(label, 'channel-name')

		label = Gtk.Label(data.language, halign=Gtk.Align.CENTER)
		name.pack_start(label, True, True, 1)
		self.widget_add_class(label, 'channel-language')

		strbox = Gtk.Box()
		self.widget_add_class(strbox, 'channel-streams')
		self.add_channel_streams(strbox, data.streams)

		outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		outer.pack_start(name, True, True, 0)
		outer.pack_start(strbox, True, True, 0)

		child = Gtk.FlowBoxChild(name='lang-' + lang_id)
		self.widget_add_class(child, 'channel-item')
		child.add(outer)
		child.show_all()

		flowbox = self.builder.get_object('flow_box_channels_list')
		flowbox.insert(child, position)

	def add_channel_streams(self, box, streams):
		position = 0

		for stream in streams:
			position = position + 1
			self.add_channel_stream_item(box, stream, position)

	def add_channel_stream_item(self, box, stream, position):
		item = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		box.pack_start(item, True, True, position)
		self.widget_add_class(item, 'channel-stream-item')

		image = self.image_from_path(stream.logo, 16)
		item.pack_start(image, False, False, 0)

		label = Gtk.Label(str(stream.rate) + 'Kbps', halign=Gtk.Align.START, margin_left=10, margin_right=10)
		item.pack_start(label, True, True, 1)
		self.widget_add_class(label, 'stream-rate')

		button = Gtk.Button.new_from_icon_name(icon_name='media-playback-start-symbolic', size=Gtk.IconSize.BUTTON)
		item.pack_start(button, False, False, 2)
		self.widget_add_class(button, 'stream-play')
		button.connect('clicked', self.events.on_stream_play_button_clicked, stream.url)

		item.show_all()


if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	player = KickoffPlayer()
	player.run()
