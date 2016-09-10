import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf


def add_widget_class(widget, classes):
	context = widget.get_style_context()

	if type(classes) not in (tuple, list):
		classes = classes.split(' ')

	for name in classes:
		context.add_class(name)


def remove_widget_children(widget):
	children = widget.get_children()

	for child in children:
		widget.remove(child)


def image_from_path(path, size=48):
	gimage = Gtk.Image(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
	pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)

	gimage.set_from_pixbuf(pixbuf)

	return gimage
