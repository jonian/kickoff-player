import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gtk, Gst, GObject

Gst.init(None)
Gst.init_check(None)


class GstBox(Gtk.Box):

  __gtype_name__ = 'GstBox'

  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.gtksink = Gst.ElementFactory.make('gtksink')
    self.pack_start(self.gtksink.props.widget, True, True, 0)
    self.gtksink.props.widget.show()

    self.playbin = Gst.ElementFactory.make('playbin')
    self.playbin.set_property('video-sink', self.gtksink)
    self.playbin.set_property('force-aspect-ratio', True)

    self.dbus = self.playbin.get_bus()
    self.dbus.add_signal_watch()
    self.dbus.connect('message', self.on_dbus_message)

  def get_state(self):
    state = self.playbin.get_state(1)
    state = list(state)[1]
    state = state.value_name.split('_')[-1]

    return state

  def open(self, url):
    self.playbin.set_property('uri', url)

  def play(self):
    self.playbin.set_state(Gst.State.PLAYING)

  def pause(self):
    self.playbin.set_state(Gst.State.PAUSED)

  def stop(self):
    self.playbin.set_state(Gst.State.READY)

  def set_volume(self, volume):
    self.playbin.set_property('volume', volume)

  def on_dbus_message(self, _bus, message):
    if message.type == Gst.MessageType.EOS:
      self.callback('READY')
      self.stop()
    elif message.type == Gst.MessageType.ERROR:
      self.callback('ERROR')
      self.stop()
