import gi
import vlc

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import add_widget_class


class VlcBox(Gtk.Box):

  __gtype_name__ = 'VlcBox'

  callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.Box.__init__(self, *args, **kwargs)

    self.canvas = Gtk.DrawingArea()
    self.pack_start(self.canvas, True, True, 0)

    self.instance = vlc.Instance()
    self.canvas.connect('realize', self.on_canvas_realized)
    self.canvas.connect('draw', self.on_canvas_draw)

    self.player = self.instance.media_player_new()
    self.player.video_set_scale(0)
    self.player.video_set_aspect_ratio('16:9')
    self.player.video_set_deinterlace('on')

    add_widget_class(self, 'player-video')

  def open(self, url):
    location = self.instance.media_new_location(url)
    self.player.set_media(location)

    self.play()

  def play(self):
    self.player.play()
    self.callback('PLAYING')

  def pause(self):
    self.player.pause()
    self.callback('PAUSED')

  def stop(self):
    self.player.stop()
    self.callback('STOPPED')

  def set_volume(self, volume):
    volume = int(round(volume * 100))
    self.player.audio_set_volume(volume)

  def on_canvas_realized(self, widget):
    xid = widget.get_property('window').get_xid()
    self.player.set_xwindow(xid)

  def on_canvas_draw(self, widget, cr):
    cr.set_source_rgb(0.0, 0.0, 0.0)
    cr.paint()
