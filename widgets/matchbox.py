import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject, Pango
from helpers.gtk import add_widget_class, image_from_path


class MatchBox(Gtk.FlowBoxChild):

	__gtype_name__ = 'MatchBox'

	fixture = GObject.property(type=object, flags=GObject.PARAM_READWRITE)
	filter_name = GObject.property(type=str, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.FlowBoxChild.__init__(self, *args, **kwargs)

		self.fixture = self.get_property('fixture')
		self.filter_name = self.get_property('filter-name')
		self.teams = None
		self.streams = None

		self.set_valign(Gtk.Align.START)
		add_widget_class(self, 'event-item')

	def set_fixture(self, data):
		self.fixture = data
		self.filter_name = getattr(self.fixture, 'competition').name
		self.add_widget_children()

	def update_fixture(self):
		refresh_data = getattr(self.fixture, 'reload')
		self.fixture = refresh_data()
		self.teams.update_fixture(self.fixture)
		self.streams.update_fixture(self.fixture)

	def add_widget_children(self):
		outer = self.add_outer_box()
		self.add(outer)

		self.show_all()

	def add_outer_box(self):
		box = Gtk.Box()
		box.set_orientation(Gtk.Orientation.VERTICAL)

		self.teams = MatchTeamsBox()
		self.teams.set_fixture(self.fixture)
		box.pack_start(self.teams, True, True, 0)

		self.streams = MatchStreamsBox()
		self.streams.set_fixture(self.fixture)
		box.pack_start(self.streams, True, True, 1)

		return box


class MatchTeamsBox(Gtk.Box):

	__gtype_name__ = 'MatchTeamsBox'

	fixture = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.Box.__init__(self, *args, **kwargs)

		self.fixture = self.get_property('fixture')
		self.score_label = None

		self.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.set_homogeneous(True)

	def set_fixture(self, data):
		self.fixture = data
		self.add_widget_children()

	def update_fixture(self, data):
		self.fixture = data
		self.update_score_label()

	def add_widget_children(self):
		home = self.add_team_box('home')
		self.pack_start(home, True, True, 0)

		score = self.add_score_box()
		self.update_score_label()
		self.pack_start(score, True, True, 1)

		away = self.add_team_box('away')
		self.pack_start(away, True, True, 2)

		self.show_all()

	def add_column_box(self, tooltip=None):
		box = Gtk.Box()
		box.set_orientation(Gtk.Orientation.VERTICAL)
		box.set_spacing(10)
		box.set_margin_top(10)
		box.set_margin_bottom(10)
		box.set_margin_left(10)
		box.set_margin_right(10)
		box.set_tooltip_text(tooltip)

		return box

	def add_team_box(self, team):
		crest = getattr(self.fixture, team + '_team').crest
		image = self.add_team_crest(crest)

		name = getattr(self.fixture, team + '_team').name
		label = self.add_team_name(name)

		box = self.add_column_box(name)
		box.pack_start(image, True, True, 0)
		box.pack_start(label, True, True, 1)

		return box

	def add_team_name(self, name):
		label = Gtk.Label(name)
		label.set_max_width_chars(25)
		label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
		label.set_margin_left(5)
		label.set_margin_right(5)

		add_widget_class(label, 'team-name')

		return label

	def add_team_crest(self, path):
		image = image_from_path(path)

		return image

	def add_score_box(self):
		score = getattr(self.fixture, 'score')
		label = self.add_score_label(score)

		box = self.add_column_box()
		box.pack_start(label, True, True, 0)

		return box

	def add_score_label(self, score):
		self.score_label = Gtk.Label(score)
		self.score_label.set_justify(Gtk.Justification.CENTER)
		self.score_label.set_halign(Gtk.Align.CENTER)
		self.score_label.set_valign(Gtk.Align.CENTER)

		add_widget_class(self.score_label, 'event-date')

		return self.score_label

	def update_score_label(self):
		if getattr(self.fixture, 'past'):
			add_widget_class(self.score_label, 'event-score')

		if getattr(self.fixture, 'today'):
			add_widget_class(self.score_label, 'event-today')

		if getattr(self.fixture, 'live'):
			add_widget_class(self.score_label, 'event-live')

		score = getattr(self.fixture, 'score')
		self.score_label.set_label(score)


class MatchStreamsBox(Gtk.Box):

	__gtype_name__ = 'MatchStreamsBox'

	fixture = GObject.property(type=object, flags=GObject.PARAM_READWRITE)

	def __init__(self, *args, **kwargs):
		Gtk.Box.__init__(self, *args, **kwargs)

		self.fixture = self.get_property('fixture')
		self.event_count = 0
		self.count_label = None
		self.more_button = None

		self.set_orientation(Gtk.Orientation.HORIZONTAL)
		add_widget_class(self, 'event-item-streams')

	def set_fixture(self, data):
		self.fixture = data
		self.event_count = getattr(self.fixture, 'events').count()
		self.add_widget_children()

	def update_fixture(self, data):
		self.fixture = data
		self.event_count = getattr(self.fixture, 'events').count()
		self.update_count_label()
		self.update_more_button()

	def add_widget_children(self):
		count = self.add_count_label()
		self.pack_start(count, False, False, 0)
		self.update_count_label()

		available = self.add_available_label()
		self.pack_start(available, False, False, 1)

		more = self.add_more_button()
		self.pack_end(more, False, False, 2)
		self.update_more_button()

		self.show_all()

	def add_available_label(self):
		label = Gtk.Label('Streams available')
		label.set_halign(Gtk.Align.START)

		return label

	def add_count_label(self):
		self.count_label = Gtk.Label(str(self.event_count))
		self.count_label.set_margin_right(10)

		add_widget_class(self.count_label, 'event-item-counter')

		return self.count_label

	def update_count_label(self):
		self.count_label.set_label(str(self.event_count))

		if self.event_count == 0:
			add_widget_class(self.count_label, 'no-streams')

	def add_more_button(self):
		kwargs = { 'icon_name': 'media-playback-start-symbolic', 'size': Gtk.IconSize.BUTTON }
		self.more_button = Gtk.Button.new_from_icon_name(**kwargs)
		# self.more_button.connect('clicked', self.on_more_button_clicked, self.fixture.events)

		add_widget_class(self.more_button, 'event-item-details')

		return self.more_button

	def update_more_button(self):
		if self.event_count == 0:
			self.more_button.set_sensitive(False)
			self.more_button.set_opacity(0)
