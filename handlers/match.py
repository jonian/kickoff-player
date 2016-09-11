import gi
import threading

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject
from helpers.gtk import filter_widget_items, remove_widget_children

from widgets.matchbox import MatchBox, MatchTeamsBox, MatchStreamBox
from widgets.filterbox import FilterBox


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

		GObject.timeout_add(10000, self.update_live_data)

	def update_matches_data(self):
		thread = threading.Thread(target=self.do_update_matches_data)
		thread.start()

	def do_update_matches_data(self):
		GObject.idle_add(self.app.toggle_reload, False)

		self.app.scores_api.save_matches()
		self.app.streams_api.save_events()

		GObject.idle_add(self.update_matches_filters)
		GObject.idle_add(self.update_matches_list)
		GObject.idle_add(self.app.toggle_reload, True)

	def update_match_data(self):
		thread = threading.Thread(target=self.do_update_match_data)
		thread.start()

	def do_update_match_data(self):
		GObject.idle_add(self.app.toggle_reload, False)

		self.app.scores_api.save_matches()
		self.app.streams_api.save_events()

		GObject.idle_add(self.update_match_details)
		GObject.idle_add(self.app.toggle_reload, True)

	def update_live_data(self):
		thread = threading.Thread(target=self.do_update_live_data)
		thread.start()

		return True

	def do_update_live_data(self):
		self.app.scores_api.save_live()
		GObject.idle_add(self.update_matches_list)

	def do_matches_filters(self):
		mlistbox = self.matches.get_object('list_box_matches_filters')
		mfilters = ['All Competitions'] + self.data.load_competitions(True, True)

		for mfilter in mfilters:
			filterbox = FilterBox(filter_name=mfilter)
			mlistbox.add(filterbox)

	def update_matches_filters(self):
		mlistbox = self.matches.get_object('list_box_matches_filters')
		mfilters = ['All Competitions'] + self.data.load_competitions(True, True)

		for item in mlistbox.get_children():
			if item.filter_name not in mfilters:
				item.destroy()

	def do_matches_list(self):
		fixtures = self.data.load_fixtures(True)
		eflowbox = self.matches.get_object('flow_box_matches_list')

		for fixture in fixtures:
			matchbox = MatchBox(fixture=fixture, callback=self.on_match_activated)
			eflowbox.add(matchbox)

	def update_matches_list(self):
		fixtures = self.data.load_fixtures(True, True)
		flowbox = self.matches.get_object('flow_box_matches_list')

		for item in flowbox.get_children():
			if item.fixture.id in fixtures:
				item.set_property('fixture', item.fixture.reload())
			else:
				item.destroy()

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

	def update_match_details(self):
		teambox = self.match.get_object('box_match_teams')
		fixture = teambox.get_children()[0].fixture.id
		fixture = self.app.data.get_fixture({ 'id': fixture })
		self.do_match_details(fixture)

	def on_header_button_reload_clicked(self, _widget):
		stack = self.stack.get_visible_child()

		if self.app.get_stack_visible_child() == self.stack:

			if stack == self.matches_box:
				self.update_matches_data()

			if stack == self.match_box:
				self.update_match_data()

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
