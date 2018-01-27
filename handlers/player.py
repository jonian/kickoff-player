import gi
import dbus

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, Gdk, GLib
from handlers.stream import StreamHandler
from widgets.gstbox import GstBox
from helpers.gtk import toggle_cursor
from helpers.utils import relative_path


class PlayerHandler(object):

  def __init__(self, app):
    self.stream = StreamHandler(self)
    self.app    = app
    self.stack  = app.player_stack

    self.sesbus = dbus.SessionBus()
    self.isaver = self.get_isaver()
    self.cookie = None

    self.url = None
    self.xid = None

    self.loading = False
    self.cstream = None

    self.is_fullscreen = False
    self.toolbar_stick = True

    self.player = Gtk.Builder()
    self.player.add_from_file(relative_path('ui/player.ui'))
    self.player.connect_signals(self)

    self.overlay = self.player.get_object('overlay_player')
    self.stack.add_named(self.overlay, 'player_video')

    self.playbin = GstBox(callback=self.update_status)
    self.overlay.add(self.playbin)
    self.playbin.connect('button-press-event', self.on_gstbox_player_button_press_event)
    self.playbin.connect('motion-notify-event', self.on_gstbox_player_motion_notify_event)

    self.status = self.player.get_object('label_player_status')
    self.status.set_text('Not playing')

    self.toolbar        = self.player.get_object('toolbar_player')
    self.volume_button  = self.player.get_object('button_volume')
    self.full_button    = self.player.get_object('button_fullscreen')
    self.restore_button = self.player.get_object('button_unfullscreen')
    self.play_button    = self.player.get_object('button_play')
    self.pause_button   = self.player.get_object('button_pause')
    self.stop_button    = self.player.get_object('button_stop')
    self.toolbar_event  = GLib.timeout_add(3000, self.toggle_toolbar, True)

  @property

  def visible(self):
    return self.stack.get_visible_child() == self.overlay

  @property

  def actionable(self):
    return self.url is not None

  def open_stream(self, stream):
    self.cstream = stream
    self.stream.open(stream.url)

    self.toggle_controls()
    self.app.set_stack_visible_child(self.stack)

  def reload_stream(self):
    GLib.idle_add(self.app.toggle_reload, False)

    self.close_stream()
    self.open_stream(self.cstream)

    GLib.idle_add(self.app.toggle_reload, True)

  def close_stream(self):
    self.stop()
    self.stream.close()

  def open(self, url):
    self.url = url
    self.playbin.open(self.url)
    self.play()

  def close(self):
    self.url = None
    self.close_stream()

  def play(self):
    self.playbin.play()

  def pause(self):
    self.playbin.pause()

  def stop(self):
    self.playbin.stop()

  def set_volume(self, volume):
    self.playbin.set_volume(volume)

  def update_status(self, status, text=None):
    labels = {
      'PLAYING': 'Playing',
      'PAUSED':  'Paused',
      'STOPPED': 'Stopped',
      'BUFFER':  'Buffering'
    }

    if status in ['PLAYING', 'BUFFER']:
      self.toggle_buttons(True)
    else:
      self.toggle_buttons(False)

    status = labels.get(status, status)
    status = status if text is None else "%s %s" % (status, text)
    self.status.set_text(status)

  def toggle_buttons(self, playing=True):
    if playing:
      self.pause_button.set_sensitive(True)
      self.stop_button.set_sensitive(True)
      self.play_button.set_sensitive(False)
    else:
      self.pause_button.set_sensitive(False)
      self.stop_button.set_sensitive(False)
      self.play_button.set_sensitive(True)

  def toggle_fullscreen(self):
    if not self.visible:
      return

    if self.is_fullscreen:
      self.restore_button.hide()
      self.full_button.show()
      self.app.window.unfullscreen()
      self.uninhibit_ssaver()

      self.is_fullscreen = False
    else:
      self.full_button.hide()
      self.restore_button.show()
      self.app.window.fullscreen()
      self.inhibit_ssaver()

      self.is_fullscreen = True

  def toggle_toolbar(self, timer=True):
    visible = self.toolbar.is_visible()

    if not self.toolbar_stick and self.actionable:
      if timer and visible:
        self.toggle_controls(True)

      if not timer and not visible:
        self.toggle_controls(False)

    return timer

  def toggle_controls(self, hide=False):
    if hide:
      self.toolbar.hide()
      toggle_cursor(self.overlay, True)
    else:
      self.toolbar.show()
      toggle_cursor(self.overlay, False)

  def get_isaver(self):
    try:
      ssaver = self.sesbus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
      isaver = dbus.Interface(ssaver, dbus_interface='org.freedesktop.ScreenSaver')
    except dbus.exceptions.DBusException:
      isaver = None

    return isaver

  def inhibit_ssaver(self):
    if self.isaver is not None and self.cookie is None:
      self.cookie = self.isaver.Inhibit('kickoff-player', 'Playing video')

  def uninhibit_ssaver(self):
    if self.isaver is not None and self.cookie is not None:
      self.isaver.UnInhibit(self.cookie)
      self.cookie = None

  def on_stream_activated(self, _widget, stream):
    self.open_stream(stream)

  def on_button_play_clicked(self, _event):
    if not self.loading and self.actionable:
      self.play()
      self.set_volume(self.volume_button.get_value())

  def on_button_pause_clicked(self, _event):
    if not self.loading and self.actionable:
      self.pause()

  def on_button_stop_clicked(self, _event):
    if not self.loading and self.actionable:
      self.stop()

  def on_button_volume_value_changed(self, _event, value):
    if not self.loading and self.actionable:
      self.set_volume(value)

  def on_window_main_key_release_event(self, _widget, event):
    stack = self.app.get_stack_visible_child()
    kname = Gdk.keyval_name(event.keyval)

    if stack == self.stack and kname == 'F11':
      self.toggle_fullscreen()

  def on_header_button_reload_clicked(self, _event):
    stack = self.app.get_stack_visible_child()

    if stack == self.stack and self.cstream is not None:
      self.reload_stream()

  def on_button_fullscreen_clicked(self, _event):
    self.toggle_fullscreen()

  def on_button_unfullscreen_clicked(self, _event):
    self.toggle_fullscreen()

  def on_gstbox_player_button_press_event(self, _widget, event):
    if event.type == Gdk.EventType._2BUTTON_PRESS:
      self.toggle_fullscreen()

  def on_gstbox_player_motion_notify_event(self, _widget, _event):
    self.toolbar_stick = False

    GLib.source_remove(self.toolbar_event)
    GLib.idle_add(self.toggle_toolbar, False)

    self.toolbar_event = GLib.timeout_add(3000, self.toggle_toolbar, True)

  def on_toolbar_player_enter_notify_event(self, _widget, _event):
    self.toolbar_stick = True
    GLib.idle_add(self.toggle_toolbar, False)
