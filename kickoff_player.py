#! /usr/bin/python3

import gi
import signal

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GObject

from handlers.data import DataHandler
from handlers.cache import CacheHandler
from handlers.match import MatchHandler
from handlers.channel import ChannelHandler
from handlers.player import PlayerHandler

from apis.onefootball import OnefootballApi
from apis.livefootball import LivefootballApi

GObject.threads_init()


class KickoffPlayer:

	def __init__(self):
		self.data = DataHandler()
		self.cache = CacheHandler()

		self.scores_api = OnefootballApi(self.data, self.cache)
		self.streams_api = LivefootballApi(self.data, self.cache)

		self.add_extra_styles('ui/styles.css')

		self.main = Gtk.Builder()
		self.main.add_from_file('ui/main.ui')
		self.main.connect_signals(self)

		self.header_back = self.main.get_object('header_button_back')
		self.header_reload = self.main.get_object('header_button_reload')
		self.main_stack = self.main.get_object('stack_main')

		self.window = self.main.get_object('window_main')
		self.window.show_all()

		self.player_stack = self.main.get_object('stack_player')
		self.player = PlayerHandler(self)

		self.matches_stack = self.main.get_object('stack_matches')
		self.matches = MatchHandler(self)

		self.channels_stack = self.main.get_object('stack_channels')
		self.channels = ChannelHandler(self)

	def run(self):
		Gtk.main()

	def quit(self):
		self.player.close()
		Gtk.main_quit()

	def add_extra_styles(self, path):
		path_style_provider = Gtk.CssProvider()
		path_style_provider.load_from_path(path)

		Gtk.StyleContext.add_provider_for_screen(
			Gdk.Screen.get_default(),
			path_style_provider,
			Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)

	def toggle_reload(self, show):
		self.header_reload.set_sensitive(show)

	def get_stack_visible_child(self):
		child = self.main_stack.get_visible_child()

		return child

	def set_stack_visible_child(self, widget):
		self.main_stack.set_visible_child(widget)

	def on_window_main_destroy(self, _event):
		self.quit()

	def on_window_main_key_release_event(self, widget, event):
		self.player.on_window_main_key_release_event(widget, event)

	def on_header_button_back_clicked(self, widget):
		self.matches.on_header_button_back_clicked(widget)

	def on_header_button_reload_clicked(self, widget):
		self.player.on_header_button_reload_clicked(widget)
		self.matches.on_header_button_reload_clicked(widget)
		self.channels.on_header_button_reload_clicked(widget)

	def on_stack_main_visible_child_notify(self, widget, params):
		self.matches.on_stack_main_visible_child_notify(widget, params)


if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL)

	player = KickoffPlayer()
	player.run()
