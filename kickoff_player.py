#! /usr/bin/python3

import gi
import signal

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GObject

from handlers.data import DataHandler
from handlers.match import MatchHandler
from handlers.channel import ChannelHandler
from handlers.player import PlayerHandler

GObject.threads_init()


class KickoffPlayer:

	def __init__(self):
		self.data = DataHandler()
		self.add_extra_styles('ui/styles.css')

		self.main = Gtk.Builder()
		self.main.add_from_file('ui/main.ui')
		self.main.connect_signals(self)

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

	def get_stack_visible_child(self):
		stack = self.main.get_object('stack_main')
		child = stack.get_visible_child()

		return child

	def set_stack_visible_child(self, widget):
		stack = self.main.get_object('stack_main')
		stack.set_visible_child(widget)

	def toggle_reload(self, show):
		button = self.main.get_object('header_button_reload')
		button.set_sensitive(show)

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
