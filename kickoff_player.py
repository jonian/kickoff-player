#! /usr/bin/python3

import gi
import signal
import argparse

gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, GLib

from handlers.data import DataHandler, StaticStream
from handlers.cache import CacheHandler
from handlers.match import MatchHandler
from handlers.channel import ChannelHandler
from handlers.player import PlayerHandler

from apis.scores import ScoresApi
from apis.streams import StreamsApi

from helpers.gtk import add_custom_css, relative_path


class KickoffPlayer(object):

  def __init__(self, cache, data):
    GLib.set_prgname('kickoff-player')
    GLib.set_application_name('Kickoff Player')

    add_custom_css('ui/styles.css')

    self.argparse = argparse.ArgumentParser(prog='kickoff-player')
    self.argparse.add_argument('url', metavar='URL', nargs='?', default=None)

    self.cache = cache
    self.data  = data

    self.scores_api  = ScoresApi(self.data, self.cache)
    self.streams_api = StreamsApi(self.data, self.cache)

    self.main = Gtk.Builder()
    self.main.add_from_file(relative_path('ui/main.ui'))
    self.main.connect_signals(self)

    self.window        = self.main.get_object('window_main')
    self.header_back   = self.main.get_object('header_button_back')
    self.header_reload = self.main.get_object('header_button_reload')
    self.main_stack    = self.main.get_object('stack_main')

    self.player_stack   = self.main.get_object('stack_player')
    self.matches_stack  = self.main.get_object('stack_matches')
    self.channels_stack = self.main.get_object('stack_channels')

    self.matches  = MatchHandler(self)
    self.channels = ChannelHandler(self)
    self.player   = PlayerHandler(self)

    GLib.timeout_add(2000, self.toggle_reload, True)
    self.open_stream_url()

  def run(self):
    self.window.show_all()
    Gtk.main()

  def quit(self):
    self.player.close()
    Gtk.main_quit()

  def open_stream_url(self):
    url = self.argparse.parse_args().url

    if url is not None:
      stream = StaticStream(url)
      self.player.open_stream(stream)

      self.set_stack_visible_child(self.player_stack)

  def toggle_reload(self, show):
    self.header_reload.set_sensitive(show)

  def get_stack_visible_child(self):
    return self.main_stack.get_visible_child()

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
    self.channels.on_stack_main_visible_child_notify(widget, params)


if __name__ == '__main__':
  signal.signal(signal.SIGINT, signal.SIG_DFL)

  cache = CacheHandler()
  data  = DataHandler()

  player = KickoffPlayer(cache, data)
  player.run()
