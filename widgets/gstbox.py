import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst, GObject
from helpers.gtk import add_widget_class

Gst.init(None)


class GstBox(Gtk.Box):

  __gtype_name__ = 'GstBox'

  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.gtksink = Gst.ElementFactory.make('gtksink')
    self.swidget = self.gtksink.props.widget
    self.pack_start(self.swidget, True, True, 0)

    self.playbin = Gst.ElementFactory.make('playbin')
    self.playbin.set_property('video-sink', self.gtksink)
    self.playbin.set_property('force-aspect-ratio', True)

    self.dbus = self.playbin.get_bus()
    self.dbus.add_signal_watch()
    self.dbus.connect('message', self.on_dbus_message)

    add_widget_class(self, 'player-video')

  def open(self, url):
    self.playbin.set_state(Gst.State.NULL)
    self.playbin.set_property('uri', url)

  def play(self):
    self.playbin.set_state(Gst.State.PLAYING)
    self.callback('PLAYING')

  def pause(self):
    self.playbin.set_state(Gst.State.PAUSED)
    self.callback('PAUSED')

  def stop(self):
    self.playbin.set_state(Gst.State.NULL)
    self.callback('STOPPED')

  def set_volume(self, volume):
    self.playbin.set_property('volume', volume)

  def on_buffering(self, message):
    percent = int(message.parse_buffering())
    self.callback('BUFFER', "%s%s" % (percent, '%'))

    if percent < 100:
      self.playbin.set_state(Gst.State.PAUSED)
    else:
      self.playbin.set_state(Gst.State.PLAYING)
      self.callback('PLAYING')

  def on_error(self, message):
    error = message.parse_error()
    self.playbin.set_state(Gst.State.READY)
    self.callback("%s.." % error[0].message)

  def on_eos(self):
    self.playbin.set_state(Gst.State.READY)
    self.callback('End of stream reached...')

  def on_clock_lost(self):
    self.playbin.set_state(Gst.State.PAUSED)
    self.playbin.set_state(Gst.State.PLAYING)

  def on_dbus_message(self, _bus, message):
    if message.type == Gst.MessageType.ERROR:
      self.on_error(message)
    elif message.type == Gst.MessageType.EOS:
      self.on_eos()
    elif message.type == Gst.MessageType.BUFFERING:
      self.on_buffering(message)
    elif message.type == Gst.MessageType.CLOCK_LOST:
      self.on_clock_lost()
