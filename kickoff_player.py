#! /usr/bin/python3

import gi
import signal

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GObject
from widgets.matchbox import MatchBox
from widgets.channelbox import ChannelBox
from widgets.filterbox import FilterBox

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

	def add_extra_styles(self, path):
		path_style_provider = Gtk.CssProvider()
		path_style_provider.load_from_path(path)

		Gtk.StyleContext.add_provider_for_screen(
			Gdk.Screen.get_default(),
			path_style_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)

	def add_events_filters(self):
		position = 0
		defaults = [Struct({ 'name': 'All Competitions' })]
		elistbox = self.builder.get_object('list_box_events_filters')
		efilters = defaults + list(self.data.load_competitions(True))

		for efilter in efilters:
			position = position + 1
			filterbox = FilterBox(filter_name=efilter.name)
			elistbox.insert(filterbox, position)

	def add_events_list(self):
		position = 0
		fixtures = self.data.load_fixtures(True)
		eflowbox = self.builder.get_object('flow_box_events_list')

		for fixture in fixtures:
			position = position + 1
			matchbox = MatchBox()
			matchbox.set_fixture(fixture)
			eflowbox.insert(matchbox, position)

	def add_event_streams(self, listbox, events):
		position = 0

		for event in events:
			position = position + 1
			# self.add_event_stream_item(listbox, event, position)

	def add_channels_filters(self):
		position = 0
		defaults = ['All Languages']
		clistbox = self.builder.get_object('list_box_channels_filters')
		cfilters = defaults + self.data.load_languages()

		for cfilter in cfilters:
			position = position + 1
			filterbox = FilterBox(filter_name=cfilter)
			clistbox.insert(filterbox, position)

	def add_channels_list(self):
		position = 0
		channels = self.data.load_channels(True)
		cflowbox = self.builder.get_object('flow_box_channels_list')

		for channel in channels:
			position = position + 1
			channbox = ChannelBox()
			channbox.set_channel(channel)
			channbox.connect('stream-activate', self.events.on_stream_activated)
			cflowbox.insert(channbox, position)


if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	player = KickoffPlayer()
	player.run()
