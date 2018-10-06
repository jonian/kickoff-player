import gi
import mpv

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import add_widget_class


class MpvBox(Gtk.Box):

  __gtype_name__ = 'MpvBox'

  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.vid_url = None
    self.stopped = False

    self.canvas = Gtk.DrawingArea()
    self.pack_start(self.canvas, True, True, 0)

    self.player = mpv.MPV(ytdl=True, input_cursor=False, cursor_autohide=False)
    self.canvas.connect('realize', self.on_canvas_realize)
    self.canvas.connect('draw', self.on_canvas_draw)

    add_widget_class(self, 'player-video')

  def open(self, url):
    self.vid_url = url
    self.player.play(url)

  def play(self):
    if self.stopped:
      self.stopped = False
      self.player.play(self.vid_url)
    else:
      self.player._set_property('pause', False)

    self.callback('PLAYING')

  def pause(self):
    self.player._set_property('pause', True)
    self.callback('PAUSED')

  def stop(self):
    self.stopped = True
    self.player.command('stop')
    self.callback('STOPPED')

  def set_volume(self, volume):
    volume = int(round(volume * 100))
    self.player._set_property('volume', volume)

  def on_canvas_realize(self, widget):
    self.player.wid = widget.get_property('window').get_xid()

  def on_canvas_draw(self, widget, cr):
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.paint()
