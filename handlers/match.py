import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, GLib
from helpers.utils import now, in_thread
from helpers.gtk import remove_widget_children, set_scroll_position

from widgets.matchbox import MatchBox, MatchTeamsBox, MatchStreamBox
from widgets.filterbox import FilterBox


class MatchHandler(object):

  def __init__(self, app):
    self.app    = app
    self.stack  = app.matches_stack
    self.filter = None

    self.matches = Gtk.Builder()
    self.matches.add_from_file('ui/matches.ui')
    self.matches.connect_signals(self)

    self.matches_box = self.matches.get_object('box_matches')
    self.stack.add_named(self.matches_box, 'matches_container')

    self.matches_filters = self.matches.get_object('list_box_matches_filters')
    self.matches_list    = self.matches.get_object('flow_box_matches_list')
    self.matches_list.set_filter_func(self.on_matches_list_row_changed)

    self.match = Gtk.Builder()
    self.match.add_from_file('ui/match.ui')
    self.match.connect_signals(self)

    self.match_box = self.match.get_object('box_match')
    self.stack.add_named(self.match_box, 'match_container')

    self.match_teams   = self.match.get_object('box_match_teams')
    self.match_streams = self.match.get_object('list_box_match_streams')

    GLib.idle_add(self.update_competitions_data)
    GLib.idle_add(self.update_teams_data)
    GLib.idle_add(self.do_matches_widgets)

    GLib.timeout_add(10000, self.update_live_data)

  def do_matches_widgets(self):
    if not self.matches_filters.get_children():
      GLib.idle_add(self.do_matches_filters)

    if not self.matches_list.get_children():
      GLib.idle_add(self.do_matches_list)

  def update_matches_widgets(self):
    if self.matches_filters.get_children():
      GLib.idle_add(self.update_matches_filters)

    if self.matches_list.get_children():
      GLib.idle_add(self.update_matches_list)

  def update_competitions_data(self):
    if not self.app.data.load_competitions():
      self.app.scores_api.save_competitions()

  def update_teams_data(self):
    if not self.app.data.load_teams():
      self.app.scores_api.save_teams()

  def update_matches_data(self):
    in_thread(target=self.do_update_matches_data)

  def do_update_matches_data(self):
    GLib.idle_add(self.app.toggle_reload, False)

    self.app.scores_api.save_matches()
    self.app.streams_api.save_events()

    GLib.idle_add(self.update_matches_widgets)
    GLib.idle_add(self.app.toggle_reload, True)

  def update_match_data(self):
    in_thread(target=self.do_update_match_data)

  def do_update_match_data(self):
    GLib.idle_add(self.app.toggle_reload, False)

    self.app.scores_api.save_matches()
    self.app.streams_api.save_events()

    GLib.idle_add(self.update_match_details)
    GLib.idle_add(self.app.toggle_reload, True)

  def update_live_data(self):
    match_items = self.matches_list.get_children()

    if match_items and match_items[0].fixture.date <= now():
      in_thread(target=self.do_update_live_data)

    return True

  def do_update_live_data(self):
    self.app.scores_api.save_live()
    GLib.idle_add(self.update_matches_list)

  def do_matches_filters(self):
    filters = self.app.data.load_matches_filters()
    remove_widget_children(self.matches_filters)

    for index, filter_name in enumerate(filters):
      GLib.timeout_add(50 * index, self.do_filter_item, filter_name)

  def do_filter_item(self, filter_name):
    filterbox = FilterBox(filter_name=filter_name)
    self.matches_filters.add(filterbox)

  def update_matches_filters(self):
    filters = self.app.data.load_matches_filters()

    for item in self.matches_filters.get_children():
      if item.filter_name not in filters:
        item.destroy()

  def do_matches_list(self):
    fixtures = self.app.data.load_fixtures(True)
    remove_widget_children(self.matches_list)

    for index, fixture in enumerate(fixtures):
      GLib.timeout_add(50 * index, self.do_match_item, fixture)

  def do_match_item(self, fixture):
    matchbox = MatchBox(fixture=fixture, callback=self.on_match_activated)
    self.matches_list.add(matchbox)

  def update_matches_list(self):
    fixtures = self.app.data.load_fixtures(True, True)

    for item in self.matches_list.get_children():
      if item.fixture.id in fixtures:
        updated = self.app.data.get_single('fixture', { 'id': item.fixture.id })
        item.set_property('fixture', updated)
      else:
        item.destroy()

  def do_match_details(self, fixture):
    remove_widget_children(self.match_teams)
    remove_widget_children(self.match_streams)

    teambox = MatchTeamsBox(fixture=fixture)
    self.match_teams.pack_start(teambox, True, True, 0)

    if not fixture.events:
      streambox = MatchStreamBox(stream=None, callback=None)
      self.match_streams.add(streambox)

    for event in fixture.events:
      streambox = MatchStreamBox(stream=event.stream, callback=self.app.player.open_stream)
      self.match_streams.add(streambox)

  def update_match_details(self):
    fixture = self.match_teams.get_children()[0].fixture.id
    fixture = self.app.data.get_single('fixture', { 'id': fixture })

    self.do_match_details(fixture)

  def on_header_button_reload_clicked(self, _widget):
    outer = self.app.get_stack_visible_child()
    inner = self.stack.get_visible_child()

    if outer != self.stack:
      return

    if inner == self.matches_box:
      self.update_matches_data()

    if inner == self.match_box:
      self.update_match_data()

  def on_header_button_back_clicked(self, widget):
    self.stack.set_visible_child(self.matches_box)
    widget.hide()

  def on_stack_main_visible_child_notify(self, widget, _params):
    outer = widget.get_visible_child()
    inner = self.stack.get_visible_child()

    if outer == self.stack and inner == self.match_box:
      self.app.header_back.show()
    else:
      self.app.header_back.hide()

  def on_match_activated(self, fixture):
    self.stack.set_visible_child(self.match_box)
    self.do_match_details(fixture)

    self.app.header_back.show()

  def on_matches_list_row_changed(self, item):
    return self.filter is None or item.filter_name == self.filter

  def on_list_box_matches_filters_row_activated(self, _listbox, item):
    self.filter = None if item.filter_name == 'All Competitions' else item.filter_name
    self.matches_list.invalidate_filter()
    set_scroll_position(self.matches_list, 0)
