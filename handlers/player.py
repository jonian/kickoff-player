import gi
import vlc

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk


class PlayerHandler(object):

	def __init__(self, app):
		self.app = app
		self.url = None
		self.xid = None

		self.widget = self.app.builder.get_object('drawing_area_player')
		self.widget.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(red=0, green=0, blue=0))
		self.widget.connect('realize', self.on_widget_realize)

		self.status = self.app.builder.get_object('label_player_status')
		self.status.set_text('Not playing')

		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()

		self.player.video_set_scale(0)
		self.player.video_set_aspect_ratio('16:9')
		self.player.video_set_deinterlace('on')

	@property

	def state(self):
		state = self.player.get_state()
		state = str(state).replace('State.', '').lower().strip()

		return state

	@property

	def actionable(self):
		if self.url is None:
			return False

		return True

	def open(self, url):
		self.url = self.instance.media_new_location(url)
		self.player.set_media(self.url)
		self.play()

	def close(self):
		self.url = None
		self.stop()

	def play(self):
		self.player.play()

	def pause(self):
		self.player.pause()

	def stop(self):
		self.player.stop()

	def set_volume(self, volume):
		if self.actionable:
			self.player.audio_set_volume(volume)

	def update_status(self, text):
		self.status.set_text(text)

	def on_widget_realize(self, widget):
		self.xid = widget.get_property('window').get_xid()
		self.player.set_xwindow(self.xid)
