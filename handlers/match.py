import gi
import threading

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.utils import Struct
from helpers.gtk import filter_widget_items, remove_widget_children

from widgets.matchbox import MatchBox, MatchTeamsBox, MatchStreamBox
from widgets.filterbox import FilterBox

from apis.onefootball import OnefootballApi
from apis.livefootball import LivefootballApi


class MatchHandler(object):

	def __init__(self, app):
		self.app = app
		self.data = app.data
		self.window = app.window
		self.stack = app.matches_stack
		self.player = app.player

		self.matches = Gtk.Builder()
		self.matches.add_from_file('ui/matches.ui')
		self.matches.connect_signals(self)

		self.matches_box = self.matches.get_object('box_matches')
		self.stack.add_named(self.matches_box, 'matches_container')

		self.match = Gtk.Builder()
		self.match.add_from_file('ui/match.ui')
		self.match.connect_signals(self)

		self.match_box = self.match.get_object('box_match')
		self.stack.add_named(self.match_box, 'match_container')

		GObject.idle_add(self.do_matches_filters)
		GObject.idle_add(self.do_matches_list)

	def update_matches_data(self):
		thread = threading.Thread(target=self.do_update_matches_data)
		thread.start()

	def do_update_matches_data(self):
		onefootball = OnefootballApi()
		onefootball.save_matches()

		livefootball = LivefootballApi()
		livefootball.save_events()

		GObject.idle_add(self.update_matches_filters)
		GObject.idle_add(self.update_matches_list)

	def do_matches_filters(self):
		defaults = [Struct({ 'name': 'All Competitions' })]
		elistbox = self.matches.get_object('list_box_matches_filters')
		efilters = defaults + list(self.data.load_competitions(True))

		for efilter in efilters:
			filterbox = FilterBox(filter_name=efilter.name)
			elistbox.add(filterbox)

	def update_matches_filters(self):
		listbox = self.matches.get_object('list_box_matches_filters')

		print(listbox)

	def do_matches_list(self):
		fixtures = self.data.load_fixtures(True)
		eflowbox = self.matches.get_object('flow_box_matches_list')

		for fixture in fixtures:
			matchbox = MatchBox(fixture=fixture, callback=self.on_match_activated)
			eflowbox.add(matchbox)

	def update_matches_list(self):
		flowbox = self.matches.get_object('flow_box_matches_list')

		print(flowbox)

	def do_match_details(self, fixture):
		box = self.match.get_object('box_match_teams')
		remove_widget_children(box)

		teambox = MatchTeamsBox(fixture=fixture)
		box.pack_start(teambox, True, True, 0)

		listbox = self.match.get_object('list_box_match_streams')
		remove_widget_children(listbox)

		if fixture.events.count() == 0:
			streambox = MatchStreamBox(stream=None, callback=None)
			listbox.add(streambox)

		for event in fixture.events:
			streambox = MatchStreamBox(stream=event.stream, callback=self.player.open_stream)
			listbox.add(streambox)

	def on_header_reload_button_clicked(self, _event):
		if self.app.get_stack_visible_child() == self.stack:
			self.update_matches_data()

	def on_header_button_back_clicked(self, widget):
		self.stack.set_visible_child(self.matches_box)
		widget.hide()

	def on_stack_main_visible_child_notify(self, widget, _params):
		button = self.app.main.get_object('header_button_back')
		vstack = widget.get_visible_child()
		vchild = self.stack.get_visible_child()

		if vstack == self.stack and vchild == self.match_box:
			button.show()
		else:
			button.hide()

	def on_match_activated(self, fixture):
		button = self.app.main.get_object('header_button_back')
		button.show()

		self.stack.set_visible_child(self.match_box)
		self.do_match_details(fixture)

	def on_list_box_matches_filters_row_activated(self, _listbox, item):
		flowbox = self.matches.get_object('flow_box_matches_list')
		filter_widget_items(self.window, flowbox, item, 'All Competitions', 'filter_name')
