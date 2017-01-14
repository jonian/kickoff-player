import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from widgets.streambox import StreamBox
from helpers.gtk import add_widget_class, remove_widget_children, image_from_path


class ChannelBox(Gtk.FlowBoxChild):

  __gtype_name__ = 'ChannelBox'
  __gsignals__ = { 'stream-activate': (GObject.SIGNAL_RUN_FIRST, None, (object,)) }

  channel = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
  filter_name = GObject.property(type=str, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.FlowBoxChild.__init__(self, *args, **kwargs)

    self.channel = self.get_property('channel')
    self.callback = self.get_property('callback')
    self.filter_name = self.get_property('filter_name')

    self.outer_box = self.do_outer_box()
    self.header_box = self.do_header_box()
    self.streams_box = self.do_streams_box()

    self.set_valign(Gtk.Align.START)
    self.connect('realize', self.on_channel_updated)
    self.connect('realize', self.on_realize)
    self.connect('notify::channel', self.on_channel_updated)

    add_widget_class(self, 'channel-item')

    self.show()

  def on_realize(self, *_args):
    self.update_outer_box()

    self.outer_box.pack_start(self.header_box, True, True, 0)
    self.outer_box.pack_start(self.streams_box, True, True, 1)

  def on_channel_updated(self, *_args):
    self.filter_name = getattr(self.channel, 'language')
    self.update_header_box()
    self.update_streams_box()

  def do_outer_box(self):
    box = Gtk.Box()
    box.set_orientation(Gtk.Orientation.VERTICAL)

    return box

  def update_outer_box(self):
    self.add(self.outer_box)
    self.outer_box.show()

  def do_header_box(self):
    header = ChannelHeaderBox(channel=self.channel)

    return header

  def update_header_box(self):
    self.header_box.set_property('channel', self.channel)

  def do_streams_box(self):
    streams = ChannelStreamsBox(channel=self.channel, callback=self.callback)

    return streams

  def update_streams_box(self):
    self.streams_box.set_property('channel', self.channel)


class ChannelHeaderBox(Gtk.Box):

  __gtype_name__ = 'ChannelHeaderBox'

  channel = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.channel = self.get_property('channel')
    self.channel_logo = self.do_channel_logo()
    self.channel_name = self.do_channel_name()
    self.channel_language = self.do_channel_language()

    self.set_orientation(Gtk.Orientation.VERTICAL)
    self.set_margin_top(10)
    self.set_margin_bottom(10)
    self.set_margin_left(10)
    self.set_margin_right(10)
    self.set_spacing(10)

    self.connect('realize', self.on_channel_updated)
    self.connect('realize', self.on_realize)
    self.connect('notify::channel', self.on_channel_updated)

    self.show()

  def on_realize(self, *_args):
    self.pack_start(self.channel_logo, False, False, 0)
    self.pack_start(self.channel_name, True, True, 1)
    self.pack_start(self.channel_language, True, True, 2)

  def on_channel_updated(self, *_args):
    self.update_channel_logo()
    self.update_channel_name()
    self.update_channel_language()

  def do_channel_logo(self):
    image = image_from_path(path='images/channel-logo.svg')
    image.set_halign(Gtk.Align.CENTER)
    image.set_valign(Gtk.Align.CENTER)

    return image

  def update_channel_logo(self):
    logo = getattr(self.channel, 'logo')
    image_from_path(path=logo, image=self.channel_logo)
    self.channel_logo.show()

  def do_channel_name(self):
    label = Gtk.Label('Unknown Channel')
    label.set_halign(Gtk.Align.CENTER)

    add_widget_class(label, 'channel-name')

    return label

  def update_channel_name(self):
    name = getattr(self.channel, 'name')
    self.channel_name.set_label(name)
    self.channel_name.show()

  def do_channel_language(self):
    label = Gtk.Label('Unknown')
    label.set_halign(Gtk.Align.CENTER)

    add_widget_class(label, 'channel-language')

    return label

  def update_channel_language(self):
    language = getattr(self.channel, 'language')
    self.channel_language.set_label(language)
    self.channel_language.show()


class ChannelStreamsBox(Gtk.Box):

  __gtype_name__ = 'ChannelStreamsBox'

  channel = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.channel = self.get_property('channel')
    self.callback = self.get_property('callback')
    self.streams = None

    self.set_orientation(Gtk.Orientation.HORIZONTAL)
    self.set_homogeneous(True)

    self.connect('realize', self.on_channel_updated)
    self.connect('notify::channel', self.on_channel_updated)

    add_widget_class(self, 'channel-streams')

    self.show()

  def on_channel_updated(self, *_args):
    self.streams = getattr(self.channel, 'streams')
    self.update_channel_streams()

  def do_channel_streams(self):
    for stream in self.streams:
      streambox = StreamBox(stream=stream, callback=self.callback, compact=True)
      self.pack_start(streambox, True, True, 0)

      add_widget_class(streambox, 'channel-stream-item')

  def update_channel_streams(self):
    remove_widget_children(self)
    self.do_channel_streams()
