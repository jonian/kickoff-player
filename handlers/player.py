import gi
import vlc

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GObject
from handlers.stream import StreamHandler


class PlayerHandler(object):

	def __init__(self, app):
		self.stream = StreamHandler(self)

		self.app = app
		self.window = app.window
		self.stack = app.player_stack

		self.url = None
		self.xid = None

		self.loading = False
		self.cstream = None

		self.is_fullscreen = False
		self.toolbar_stick = True

		self.player = Gtk.Builder()
		self.player.add_from_file('ui/player.ui')
		self.player.connect_signals(self)

		self.overlay = self.player.get_object('overlay_player')
		self.stack.add_named(self.overlay, 'player_video')

		self.widget = self.player.get_object('drawing_area_player')
		self.widget.connect('realize', self.on_widget_realized)

		self.status = self.player.get_object('label_player_status')
		self.status.set_text('Not playing')

		self.instance = vlc.Instance()
		self.playbin = self.instance.media_player_new()

		self.playbin.video_set_scale(0)
		self.playbin.video_set_aspect_ratio('16:9')
		self.playbin.video_set_deinterlace('on')

		GObject.timeout_add(3000, self.toggle_toolbar, True)

	@property

	def visible(self):
		if self.stack.get_visible_child() == self.overlay:
			return True

		return False

	@property

	def state(self):
		state = self.playbin.get_state()
		state = str(state).replace('State.', '').lower().strip()

		return state

	@property

	def actionable(self):
		if self.url is None:
			return False

		return True

	def open_stream(self, stream):
		self.cstream = stream
		self.stream.open(stream.url)

		self.toggle_toolbar(False)
		self.app.set_stack_visible_child(self.stack)

	def reload_stream(self):
		GObject.idle_add(self.app.toggle_reload, False)

		self.close_stream()
		self.open_stream(self.cstream)

		GObject.idle_add(self.app.toggle_reload, True)

	def close_stream(self):
		self.url = None
		self.stop()
		self.stream.close()

	def open(self, url):
		self.url = self.instance.media_new_location(url)
		self.playbin.set_media(self.url)
		self.play()

	def close(self):
		self.close_stream()

	def play(self):
		self.playbin.play()

	def pause(self):
		self.playbin.pause()

	def stop(self):
		self.playbin.stop()

	def set_volume(self, volume):
		if self.actionable:
			self.playbin.audio_set_volume(volume)

	def update_status(self, text=None):
		if not self.loading and text is None:
			labels = {
				'playing': 'Playing',
				'paused': 'Paused',
				'stopped': 'Stopped'
			}

			text = labels.get(self.state, 'Not playing')

		self.status.set_text(text)

		return False

	def toggle_fullscreen(self):
		if not self.visible:
			return False

		enable = self.player.get_object('button_fullscreen')
		disable = self.player.get_object('button_unfullscreen')

		if self.is_fullscreen:
			disable.hide()
			enable.show()
			self.window.unfullscreen()

			self.is_fullscreen = False
		else:
			enable.hide()
			disable.show()
			self.window.fullscreen()

			self.is_fullscreen = True

	def toggle_toolbar(self, timer=True):
		toolbar = self.player.get_object('toolbar_player')
		visible = toolbar.is_visible()

		if not self.toolbar_stick and self.actionable:
			if timer and visible:
				toolbar.hide()

			if not timer and not visible:
				toolbar.show()

		return timer

	def on_widget_realized(self, widget):
		self.xid = widget.get_property('window').get_xid()
		self.playbin.set_xwindow(self.xid)

	def on_stream_activated(self, _widget, stream):
		self.open_stream(stream)

	def on_button_play_clicked(self, _event):
		if not self.loading:
			volume = self.player.get_object('button_volume').get_value()
			volume = int(round(volume * 100))

			self.play()
			self.set_volume(volume)
			GObject.idle_add(self.update_status)

	def on_button_pause_clicked(self, _event):
		if not self.loading:
			self.pause()
			GObject.idle_add(self.update_status)

	def on_button_stop_clicked(self, _event):
		if not self.loading:
			self.stop()
			GObject.idle_add(self.update_status)

	def on_button_volume_value_changed(self, _event, value):
		volume = int(round(value * 100))
		self.set_volume(volume)

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

	def on_drawing_area_player_motion_notify_event(self, _widget, _event):
		self.toolbar_stick = False
		GObject.idle_add(self.toggle_toolbar, False)

	def on_toolbar_player_enter_notify_event(self, _widget, _event):
		self.toolbar_stick = True
		GObject.idle_add(self.toggle_toolbar, False)
