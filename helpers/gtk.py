import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GdkPixbuf


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


def remove_widget_children(widget):
	children = widget.get_children()

	for child in children:
		child.destroy()


def filter_widget_items(window, container, selected, default, attr):
	selected = getattr(selected, attr)

	for child in container.get_children():
		if selected == default or getattr(child, attr) == selected:
			child.show()
		else:
			child.hide()

	window.queue_resize_no_redraw()


def image_from_path(path, size=48, image=None):
	gimage = Gtk.Image() if image is None else image
	pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, size, size, True)

	gimage.set_from_pixbuf(pixbuf)

	return gimage
