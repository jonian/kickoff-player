import gi
import threading

gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, GLib
from helpers.gtk import filter_widget_items, remove_widget_children

from widgets.channelbox import ChannelBox
from widgets.filterbox import FilterBox


class ChannelHandler(object):

  def __init__(self, app):
    self.app   = app
    self.stack = app.channels_stack

    self.channels = Gtk.Builder()
    self.channels.add_from_file('ui/channels.ui')
    self.channels.connect_signals(self)

    self.channels_box = self.channels.get_object('box_channels')
    self.stack.add_named(self.channels_box, 'channels_container')

    self.channels_filters = self.channels.get_object('list_box_channels_filters')
    self.channels_list    = self.channels.get_object('flow_box_channels_list')

  def do_channels_widgets(self):
    if not self.channels_filters.get_children():
      GLib.idle_add(self.do_channels_filters)

    if not self.channels_list.get_children():
      GLib.idle_add(self.do_channels_list)

  def update_channels_widgets(self):
    if self.channels_filters.get_children():
      GLib.idle_add(self.update_channels_filters)

    if self.channels_list.get_children():
      GLib.idle_add(self.update_channels_list)

  def update_channels_data(self):
    thread = threading.Thread(target=self.do_update_channels_data)
    thread.start()

  def do_update_channels_data(self):
    GLib.idle_add(self.app.toggle_reload, False)

    self.app.streams_api.save_streams()

    GLib.idle_add(self.do_channels_widgets)
    GLib.idle_add(self.update_channels_widgets)
    GLib.idle_add(self.app.toggle_reload, True)

  def do_channels_filters(self):
    filters = self.app.data.load_channels_filters()
    remove_widget_children(self.channels_filters)

    for index, filter_name in enumerate(filters):
      GLib.timeout_add(50 * index, self.do_filter_item, filter_name)

  def do_filter_item(self, filter_name):
    filterbox = FilterBox(filter_name=filter_name)
    self.channels_filters.add(filterbox)

  def update_channels_filters(self):
    filters = self.app.data.load_channels_filters()

    for item in self.channels_filters.get_children():
      if item.filter_name not in filters:
        item.destroy()

  def do_channels_list(self):
    channels = self.app.data.load_channels(True)
    remove_widget_children(self.channels_list)

    for index, channel in enumerate(channels):
      GLib.timeout_add(50 * index, self.do_channel_item, channel)

  def do_channel_item(self, channel):
    channbox = ChannelBox(channel=channel, callback=self.app.player.open_stream)
    self.channels_list.add(channbox)

  def update_channels_list(self):
    channels = self.app.data.load_channels(True, True)

    for item in self.channels_list.get_children():
      if item.channel.id in channels:
        updated = self.app.data.get_channel({ 'id': item.channel.id })
        item.set_property('channel', updated)
      else:
        item.destroy()

  def on_stack_main_visible_child_notify(self, _widget, _params):
    if self.app.get_stack_visible_child() == self.stack:
      self.do_channels_widgets()

  def on_header_button_reload_clicked(self, _event):
    if self.app.get_stack_visible_child() == self.stack:
      self.update_channels_data()

  def on_list_box_channels_filters_row_activated(self, _listbox, item):
    filter_widget_items(self.app.window, self.channels_list, item, 'All Languages', 'filter_name')
