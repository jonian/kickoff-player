import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject, Pango


class FilterBox(Gtk.ListBoxRow):

  __gtype_name__ = 'FilterBox'

  filter_name = GObject.property(type=str, flags=GObject.PARAM_READWRITE)

  def __init__(self, *args, **kwargs):
    Gtk.ListBoxRow.__init__(self, *args, **kwargs)

    self.filter_name  = self.get_property('filter-name')
    self.filter_label = self.do_filter_label()

    self.connect('realize', self.on_filter_name_updated)
    self.connect('notify::filter_name', self.on_filter_name_updated)

    self.show()

  def on_filter_name_updated(self, *_args):
    self.update_filter_label()

  def do_filter_label(self):
    label = Gtk.Label(None)
    label.set_justify(Gtk.Justification.LEFT)
    label.set_halign(Gtk.Align.START)
    label.set_max_width_chars(25)
    label.set_ellipsize(Pango.EllipsizeMode.END)
    label.set_margin_top(10)
    label.set_margin_bottom(10)
    label.set_margin_left(10)
    label.set_margin_right(10)

    return label

  def update_filter_label(self):
    self.filter_label.set_label(self.filter_name)
    self.filter_label.show()
    self.add(self.filter_label)
