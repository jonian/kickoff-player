import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import add_widget_class, image_from_path
from widgets.streambox import StreamBox


class ChannelBox(Gtk.FlowBoxChild):

	__gtype_name__ = 'ChannelBox'
	__gsignals__ = { 'stream-activate': (GObject.SIGNAL_RUN_FIRST, None, (object,)) }

	channel = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	filter_name = GObject.property(type=str, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.FlowBoxChild.__init__(self, *args, **kwargs)

		self.channel = self.get_property('channel')
		self.filter_name = self.get_property('filter-name')
		self.header = None
		self.streams = None

		self.set_valign(Gtk.Align.START)
		add_widget_class(self, 'channel-item')

	def set_channel(self, data):
		self.channel = data
		self.filter_name = getattr(self.channel, 'language')
		self.add_widget_children()

	def update_channel(self):
		refresh_data = getattr(self.channel, 'reload')
		self.channel = refresh_data()
		self.header.update_channel(self.channel)
		self.streams.update_channel(self.channel)

	def add_widget_children(self):
		outer = self.add_outer_box()
		self.add(outer)

		self.show_all()

	def add_outer_box(self):
		box = Gtk.Box()
		box.set_orientation(Gtk.Orientation.VERTICAL)

		self.header = ChannelHeaderBox()
		self.header.set_channel(self.channel)
		box.pack_start(self.header, True, True, 0)

		self.streams = ChannelStreamsBox(eventbox=self)
		self.streams.set_channel(self.channel)
		box.pack_start(self.streams, True, True, 1)

		return box


class ChannelHeaderBox(Gtk.Box):

	__gtype_name__ = 'ChannelHeaderBox'

	channel = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.Box.__init__(self, *args, **kwargs)

		self.channel = self.get_property('channel')

		self.set_orientation(Gtk.Orientation.VERTICAL)
		self.set_margin_top(10)
		self.set_margin_bottom(10)
		self.set_margin_left(10)
		self.set_margin_right(10)
		self.set_spacing(10)

	def set_channel(self, data):
		self.channel = data
		self.add_widget_children()

	def update_channel(self, data):
		self.channel = data

	def add_widget_children(self):
		logo = self.add_channel_logo()
		self.pack_start(logo, False, False, 0)

		name = self.add_channel_name()
		self.pack_start(name, True, True, 1)

		language = self.add_channel_language()
		self.pack_start(language, True, True, 2)

		self.show_all()

	def add_channel_name(self):
		label = Gtk.Label(getattr(self.channel, 'name'))
		label.set_halign(Gtk.Align.CENTER)

		add_widget_class(label, 'channel-name')

		return label

	def add_channel_language(self):
		label = Gtk.Label(getattr(self.channel, 'language'))
		label.set_halign(Gtk.Align.CENTER)

		add_widget_class(label, 'channel-language')

		return label

	def add_channel_logo(self):
		image = image_from_path(getattr(self.channel, 'logo'))

		return image


class ChannelStreamsBox(Gtk.Box):

	__gtype_name__ = 'ChannelStreamsBox'

	channel = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	eventbox = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.Box.__init__(self, *args, **kwargs)

		self.channel = self.get_property('channel')
		self.eventbox = self.get_property('eventbox')
		self.streams = None

		self.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.set_homogeneous(True)
		add_widget_class(self, 'channel-streams')

	def set_channel(self, data):
		self.channel = data
		self.streams = getattr(self.channel, 'streams')
		self.add_widget_children()

	def update_channel(self, data):
		self.channel = data
		self.streams = getattr(self.channel, 'streams')

	def add_widget_children(self):
		position = 0

		for stream in self.streams:
			position = position + 1
			streambox = StreamBox(stream=stream, eventbox=self.eventbox, compact=True)
			self.pack_start(streambox, True, True, position)

			add_widget_class(streambox, 'channel-stream-item')

		self.show_all()
