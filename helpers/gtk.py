import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GLib', '2.0')

from gi.repository import Gtk, Gdk, GLib, GdkPixbuf


def add_widget_class(widget, classes):
  context = widget.get_style_context()

  if type(classes) not in (tuple, list):
    classes = classes.split(' ')

  for name in classes:
    context.add_class(name)


def remove_widget_class(widget, classes):
  context = widget.get_style_context()

  if type(classes) not in (tuple, list):
    classes = classes.split(' ')

  for name in classes:
    context.remove_class(name)


def add_widget_custom_css(widget, style):
  screen   = Gdk.Screen.get_default()
  priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
  provider = Gtk.CssProvider()
  context  = widget.get_style_context()

  if os.path.exists(style):
    provider.load_from_path(style)
  else:
    provider.load_from_data(style.encode())

  context.add_provider(provider, priority)


def add_custom_css(style):
  screen   = Gdk.Screen.get_default()
  priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
  provider = Gtk.CssProvider()

  if os.path.exists(style):
    provider.load_from_path(style)
  else:
    provider.load_from_data(style.encode())

  Gtk.StyleContext.add_provider_for_screen(screen, provider, priority)


def remove_widget_children(widget):
  children = widget.get_children()

  for child in children:
    child.destroy()


def image_from_path(path, size=48, image=None):
  gimage = Gtk.Image() if image is None else image

  try:
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)
    gimage.set_from_pixbuf(pixbuf)
  except GLib.Error:
    pass

  return gimage


def toggle_cursor(widget, hide=False):
  window = widget.get_window()

  if window:
    blank  = Gdk.CursorType.BLANK_CURSOR
    cursor = Gdk.Cursor(blank) if hide else None
    window.set_cursor(cursor)
