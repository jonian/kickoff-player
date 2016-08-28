import gi
import threading

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import Gtk, Gdk, GObject
from handlers.crests import CrestHandler
from apis.football import FootballApi
from apis.livescore import LivescoreApi
from apis.streamsports import StreamsportsApi
from apis.livefootball import LivefootballApi


class EventHandler:

	def __init__(self, app):
		self.app = app
		self.builder = app.builder
		self.window = app.window
		self.player = app.player
		self.stream = app.stream

		self.is_fullscreen = False
		self.toolbar_stick = True

		GObject.timeout_add(3000, self.player_toolbar_toggle, True)

	def focused_stack_child(self, stack):
		stack = self.builder.get_object(stack)
		visible = Gtk.Buildable.get_name(stack.get_visible_child())

		return visible

	def player_fullscreen_toggle(self):
		if self.focused_stack_child('stack_main') == 'overlay_player':
			enable = self.builder.get_object('header_fullscreen_button')
			disable = self.builder.get_object('header_unfullscreen_button')

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

	def player_toolbar_toggle(self, timer=True):
		toolbar = self.builder.get_object('toolbar_player')
		visible = toolbar.is_visible()

		if not self.toolbar_stick and self.player.actionable:
			if timer and visible:
				toolbar.hide()

			if not timer and not visible:
				toolbar.show()

		return timer

	def player_set_volume(self, volume):
		self.player.set_volume(volume)

	def player_set_status(self):
		if not self.stream.loading:
			labels = {
				'playing': 'Playing',
				'paused': 'Paused',
				'stopped': 'Stopped'
			}

			label = labels.get(self.player.state, 'Not playing')
			self.player.update_status(label)

		return False

	def category_filter_widgets(self, category, prefix, container):
		all_items = prefix + 'all'

		if category == all_items:
			container.show_all()
		else:
			for child in container.get_children():
				if child.get_name() == category:
					child.show()
				else:
					child.hide()

		self.window.queue_resize_no_redraw()

	def stack_set_focus_child(self, stack, child):
		if child is not None:
			box = self.builder.get_object(child)
			stack = self.builder.get_object(stack)
			stack.set_visible_child(box)

	def main_stack_set_focus(self, child):
		stacks = {
			'player': 'overlay_player',
			'events': 'stack_events',
			'channels': 'box_channels'
		}

		item = stacks.get(child, None)
		self.stack_set_focus_child('stack_main', item)

	def events_stack_set_focus(self, child):
		stacks = {
			'events': 'box_events',
			'event': 'box_event'
		}

		item = stacks.get(child, None)
		self.stack_set_focus_child('stack_events', item)

	def header_button_back_toggle(self, show):
		button = self.builder.get_object('header_button_back')

		if show:
			button.show()
		else:
			button.hide()

	def update_events(self):
		football = FootballApi()
		football.save_fixtures()

		crests = CrestHandler()
		crests.load_all_crests()

		livescore = LivescoreApi()
		livescore.update_fixtures()

		# streamsports = StreamsportsApi()
		# streamsports.save_events()

		GObject.idle_add(self.refresh_events_stack)

	def refresh_events_stack(self):
		listbox = self.builder.get_object('list_box_events_filters')
		self.app.widget_remove_children(listbox)
		self.app.add_events_filters()

		flowbox = self.builder.get_object('flow_box_events_list')
		self.app.widget_remove_children(flowbox)
		self.app.add_events_list()

	def update_channels(self):
		livefootball = LivefootballApi()
		livefootball.save_channels()
		livefootball.save_streams()

		GObject.idle_add(self.refresh_channels_stack)

	def refresh_channels_stack(self):
		listbox = self.builder.get_object('list_box_channels_filters')
		self.app.widget_remove_children(listbox)
		self.app.add_channels_filters()

		flowbox = self.builder.get_object('flow_box_channels_list')
		self.app.widget_remove_children(flowbox)
		self.app.add_channels_list()

	def refresh_event_stack(self, data):
		box = self.builder.get_object('box_event_teams')
		self.app.widget_remove_children(box)
		self.app.add_event_teams(box, data)

		listbox = self.builder.get_object('list_box_event_streams')
		self.app.widget_remove_children(listbox)
		self.app.add_event_streams(listbox, data.events)

	def on_window_main_destroy(self, _event):
		self.player.close()
		self.stream.close()
		self.app.quit()

	def on_window_main_key_release_event(self, _widget, event):
		if Gdk.keyval_name(event.keyval) == 'F11':
			self.player_fullscreen_toggle()

	def on_button_play_clicked(self, _event):
		if not self.stream.loading:
			volume = self.builder.get_object('button_volume').get_value()
			volume = int(round(volume * 100))

			self.player.play()
			self.player_set_volume(volume)
			GObject.idle_add(self.player_set_status)

	def on_button_pause_clicked(self, _event):
		if not self.stream.loading:
			self.player.pause()
			GObject.idle_add(self.player_set_status)

	def on_button_stop_clicked(self, _event):
		if not self.stream.loading:
			self.player.stop()
			self.stream.close()
			GObject.idle_add(self.player_set_status)

	def on_button_volume_value_changed(self, _event, value):
		volume = int(round(value * 100))

		self.player_set_volume(volume)

	def on_header_fullscreen_button_clicked(self, _event):
		self.player_fullscreen_toggle()

	def on_header_unfullscreen_button_clicked(self, _event):
		self.player_fullscreen_toggle()

	def on_drawing_area_player_motion_notify_event(self, _widget, _event):
		self.toolbar_stick = False
		GObject.idle_add(self.player_toolbar_toggle, False)

	def on_toolbar_player_enter_notify_event(self, _widget, _event):
		self.toolbar_stick = True
		GObject.idle_add(self.player_toolbar_toggle, False)

	def on_list_box_events_filters_row_activated(self, _listbox, item):
		flowbox = self.builder.get_object('flow_box_events_list')
		comp_id = item.get_name()

		GObject.idle_add(self.category_filter_widgets, comp_id, 'comp-', flowbox)

	def on_list_box_channels_filters_row_activated(self, _listbox, item):
		flowbox = self.builder.get_object('flow_box_channels_list')
		lang_id = item.get_name()

		GObject.idle_add(self.category_filter_widgets, lang_id, 'lang-', flowbox)

	def on_header_button_back_clicked(self, _event):
		self.header_button_back_toggle(False)
		self.events_stack_set_focus('events')

	def on_header_reload_button_clicked(self, _event):
		if self.focused_stack_child('stack_main') == 'box_channels':
			thread = threading.Thread(target=self.update_channels)
			thread.start()

		if self.focused_stack_child('stack_main') == 'stack_events':
			if self.focused_stack_child('stack_events') == 'box_events':
				thread = threading.Thread(target=self.update_events)
				thread.start()

	def on_event_details_button_clicked(self, _widget, data):
		self.refresh_event_stack(data)

		self.events_stack_set_focus('event')
		self.header_button_back_toggle(True)

	def on_stream_play_button_clicked(self, _widget, url):
		self.main_stack_set_focus('player')
		self.stream.open(url)
