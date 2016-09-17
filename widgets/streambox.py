import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import add_widget_class, image_from_path


class StreamBox(Gtk.Box):

	__gtype_name__ = 'StreamBox'

	stream = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	callback = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	compact = GObject.property(type=bool, default=False, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.Box.__init__(self, *args, **kwargs)

		self.stream = self.get_property('stream')
		self.callback = self.get_property('callback')
		self.compact = self.get_property('compact')

		self.stream_name = self.do_stream_name()
		self.stream_rate = self.do_stream_rate()
		self.stream_logo = self.do_stream_logo()
		self.stream_lang = self.do_stream_language()
		self.play_button = self.do_play_button()

		self.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.connect('realize', self.on_realized)
		self.connect('notify::stream', self.on_stream_updated)

		self.show()

	def on_realized(self, *_args):
		self.on_stream_updated(_args)

		self.pack_start(self.stream_lang, False, False, 0)
		self.pack_start(self.stream_logo, False, False, 1)
		self.pack_start(self.stream_name, False, False, 2)
		self.pack_end(self.play_button, False, False, 0)
		self.pack_end(self.stream_rate, False, False, 1)

	def on_stream_updated(self, *_args):
		self.update_stream_language()
		self.update_stream_logo()
		self.update_stream_name()
		self.update_play_button()
		self.update_stream_rate()

	def do_stream_logo(self):
		image = image_from_path(path='images/acestream.svg', size=16)
		image.set_halign(Gtk.Align.CENTER)
		image.set_valign(Gtk.Align.CENTER)
		image.set_margin_right(10)

		add_widget_class(image, 'stream-image')

		return image

	def update_stream_logo(self):
		logo = getattr(self.stream, 'logo')
		image_from_path(path=logo, size=16, image=self.stream_logo)
		self.stream_logo.show()

	def do_stream_language(self):
		label = Gtk.Label('Unknown')
		label.set_halign(Gtk.Align.START)
		label.set_margin_right(10)

		add_widget_class(label, 'stream-language')

		return label

	def update_stream_language(self):
		language = getattr(self.stream, 'language')
		self.stream_lang.set_label(language)

		if self.compact:
			self.stream_lang.hide()
		else:
			self.stream_lang.show()

	def do_stream_rate(self):
		label = Gtk.Label('0Kbps')
		label.set_halign(Gtk.Align.END)
		label.set_margin_right(10)

		add_widget_class(label, 'stream-rate')

		return label

	def update_stream_rate(self):
		ratio = str(getattr(self.stream, 'rate')) + 'Kbps'
		self.stream_rate.set_label(ratio)
		self.stream_rate.show()

	def do_stream_name(self):
		label = Gtk.Label('Unknown Channel')
		label.set_halign(Gtk.Align.START)
		label.set_margin_right(10)

		add_widget_class(label, 'stream-name')

		return label

	def update_stream_name(self):
		chan = getattr(self.stream, 'channel')
		name = 'Unknown Channel' if chan is None else getattr(chan, 'name')
		self.stream_name.set_label(name)

		if self.compact:
			self.stream_name.hide()
		else:
			self.stream_name.show()

	def do_play_button(self):
		kwargs = { 'icon_name': 'media-playback-start-symbolic', 'size': Gtk.IconSize.BUTTON }
		button = Gtk.Button.new_from_icon_name(**kwargs)
		button.set_halign(Gtk.Align.END)
		button.connect('clicked', self.on_play_button_clicked, self.stream)

		add_widget_class(button, 'stream-play')

		return button

	def update_play_button(self):
		self.play_button.show()

	def on_play_button_clicked(self, _widget, stream):
		self.callback(stream)
