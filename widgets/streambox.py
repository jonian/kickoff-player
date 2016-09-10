import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import add_widget_class, image_from_path


class StreamBox(Gtk.Box):

	__gtype_name__ = 'StreamBox'

	stream = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	eventbox = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	compact = GObject.property(type=bool, default=False, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.Box.__init__(self, *args, **kwargs)

		self.stream = self.get_property('stream')
		self.eventbox = self.get_property('eventbox')
		self.compact = self.get_property('compact')

		self.stream_name = self.do_stream_name()
		self.stream_rate = self.do_stream_rate()
		self.stream_logo = self.do_stream_logo()
		self.stream_lang = self.do_stream_language()
		self.play_button = self.do_play_button()

		self.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.connect('realize', self.on_realized)

		self.show()

	def on_realized(self, *_args):
		self.do_widget_children()

	def do_widget_children(self):
		if not self.compact:
			self.pack_start(self.stream_lang, False, False, 0)

		self.pack_start(self.stream_logo, False, False, 1)

		if not self.compact:
			self.pack_start(self.stream_name, False, False, 2)

		self.pack_end(self.play_button, False, False, 0)
		self.pack_end(self.stream_rate, False, False, 1)

	def do_stream_logo(self):
		image = image_from_path(getattr(self.stream, 'logo'), 16)
		image.set_margin_right(10)
		image.show()

		add_widget_class(image, 'stream-image')

		return image

	def do_stream_language(self):
		label = Gtk.Label(getattr(self.stream, 'language'))
		label.set_halign(Gtk.Align.START)
		label.set_margin_right(10)
		label.show()

		add_widget_class(label, 'stream-language')

		return label

	def do_stream_rate(self):
		ratio = getattr(self.stream, 'rate')
		label = Gtk.Label(str(ratio) + 'Kbps')
		label.set_halign(Gtk.Align.END)
		label.set_margin_right(10)
		label.show()

		add_widget_class(label, 'stream-rate')

		return label

	def do_stream_name(self):
		cname = self.parse_channel_name()
		label = Gtk.Label(cname)
		label.set_halign(Gtk.Align.START)
		label.set_margin_right(10)
		label.show()

		add_widget_class(label, 'stream-name')

		return label

	def do_play_button(self):
		kwargs = { 'icon_name': 'media-playback-start-symbolic', 'size': Gtk.IconSize.BUTTON }
		button = Gtk.Button.new_from_icon_name(**kwargs)
		button.set_halign(Gtk.Align.END)
		button.connect('clicked', self.on_play_button_clicked, self.stream)
		button.show()

		add_widget_class(button, 'stream-play')

		return button

	def on_play_button_clicked(self, _widget, stream):
		self.eventbox.emit('stream-activate', stream)

	def parse_channel_name(self):
		chan = getattr(self.stream, 'channel')
		name = 'Unknown Channel' if chan is None else getattr(chan, 'name')

		return name
