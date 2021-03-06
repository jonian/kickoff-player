import gi
import time

gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, GLib
from helpers.utils import in_thread, relative_path
from helpers.gtk import remove_widget_children, set_scroll_position, run_generator

from widgets.channelbox import ChannelBox
from widgets.filterbox import FilterBox


class ChannelHandler(object):

  def __init__(self, app):
    self.app    = app
    self.stack  = app.channels_stack
    self.filter = None

    self.channels = Gtk.Builder()
    self.channels.add_from_file(relative_path('ui/channels.ui'))
    self.channels.connect_signals(self)

    self.channels_box = self.channels.get_object('box_channels')
    self.stack.add_named(self.channels_box, 'channels_container')

    self.channels_filters = self.channels.get_object('list_box_channels_filters')
    self.channels_list    = self.channels.get_object('flow_box_channels_list')
    self.channels_list.set_filter_func(self.on_channels_list_row_changed)

    GLib.idle_add(self.do_initial_setup)

  @property

  def visible(self):
    return self.app.get_stack_visible_child() == self.stack

  def initial_setup(self):
    if not self.app.data.load_channels():
      self.update_channels_data()

  def do_initial_setup(self):
    in_thread(target=self.initial_setup)

  def do_channels_widgets(self):
    if not self.channels_filters.get_children():
      run_generator(self.do_channels_filters)

    if not self.channels_list.get_children():
      run_generator(self.do_channels_list)

  def update_channels_widgets(self):
    if self.channels_filters.get_children():
      run_generator(self.update_channels_filters)

    if self.channels_list.get_children():
      run_generator(self.update_channels_list)

  def update_channels_data(self):
    in_thread(target=self.do_update_channels_data)

  def do_update_channels_data(self):
    GLib.idle_add(self.app.toggle_reload, False)

    self.app.streams_api.save_channels()
    time.sleep(5)

    GLib.idle_add(self.do_channels_widgets)
    GLib.idle_add(self.update_channels_widgets)
    GLib.idle_add(self.app.toggle_reload, True)

  def do_channels_filters(self):
    filters = self.app.data.load_channels_filters()
    remove_widget_children(self.channels_filters)

    for filter_name in filters:
      self.do_filter_item(filter_name)
      yield True

  def do_filter_item(self, filter_name):
    filterbox = FilterBox(filter_name=filter_name, filter_all='All Languages')
    self.channels_filters.add(filterbox)

    if not self.channels_filters.get_selected_row():
      self.channels_filters.select_row(filterbox)

  def update_channels_filters(self):
    filters = self.app.data.load_channels_filters()

    for item in self.channels_filters.get_children():
      if item.filter_name not in filters:
        item.destroy()

      yield True

  def do_channels_list(self):
    channels = self.app.data.load_channels(True)
    remove_widget_children(self.channels_list)

    for channel in channels:
      self.do_channel_item(channel)
      yield True

  def do_channel_item(self, channel):
    channbox = ChannelBox(channel=channel, callback=self.app.player.open_stream)
    self.channels_list.add(channbox)

  def update_channels_list(self):
    channels = self.app.data.load_channels(True, True)

    for item in self.channels_list.get_children():
      if item.channel.id in channels:
        updated = self.app.data.get_single('channel', { 'id': item.channel.id })
        item.set_property('channel', updated)
      else:
        item.destroy()

      yield True

  def on_stack_main_visible_child_notify(self, _widget, _params):
    if self.visible:
      self.do_channels_widgets()

  def on_header_button_reload_clicked(self, _event):
    if self.visible:
      self.update_channels_data()

  def on_channels_list_row_changed(self, item):
    return self.filter is None or item.filter_name == self.filter

  def on_list_box_channels_filters_row_activated(self, _listbox, item):
    self.filter = item.filter_value

    self.channels_list.invalidate_filter()
    set_scroll_position(self.channels_list, 0, 'vertical', self.app.window)
