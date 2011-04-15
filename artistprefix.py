# -*- coding: utf8 -*-
#
# artistprefix.py
#
# Copyright (C) 2011 Graham White <graham_alton@hotmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import rhythmdb, rb
import re
import gtk
import gconf

DEFAULT_IGNORE = ['The','El','La','Los','Las','Le','Les']

GCONF_KEYS = {'ignore': '/apps/rhythmbox/plugins/artistprefix/ignore'}

class ArtistPrefix(rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)


	def on_artist_prefix_query(self, model, path, iter):
		# note: path and iter are effectively useless as a gtkTree doesn't populate the row on row-insert
		# see GTK documentation for row-inserted signal for more info
		# so we simply iterate over the model instead
		for row in model:
			entry = row[0]
			artist_sort = re.sub('^.+?\s','',self.db.entry_get(entry, rhythmdb.PROP_ARTIST),1,re.I)
			self.db.set(entry,rhythmdb.PROP_ARTIST_SORTNAME,artist_sort)
			self.db.commit()
			model.remove_entry(entry)


	def activate (self, shell):
		self.gconf = gconf.client_get_default()

		ignore_list = self.get_ignore_list()

		self.db = shell.props.db
		query = self.db.query_new()

		for i, ignore in enumerate(ignore_list):
			# append query from the ignore list ANDed with a blank sortname
			self.db.query_append(query,[rhythmdb.QUERY_PROP_PREFIX,rhythmdb.PROP_ARTIST,ignore + ' '],
                                                   [rhythmdb.QUERY_PROP_EQUALS,rhythmdb.PROP_ARTIST_SORTNAME,''])

			if (i != len(ignore_list)-1):
				# if we've got more queries coming add a disjunction (which does a logical OR with the next query)
				self.db.query_append(query, [rhythmdb.QUERY_DISJUNCTION])

		self.artist_prefix_query = self.db.query_model_new(query)
		self.db.do_full_query_async_parsed(self.artist_prefix_query, query)
		self.artist_prefix_query.connect('row-inserted',self.on_artist_prefix_query)


	def deactivate(self, shell):
		del self.artist_prefix_query
		del self.db
		del self.gconf


	def get_ignore_list(self):
		# grab the ignore list from gconf
		ignore_list = self.gconf.get_list(GCONF_KEYS['ignore'], gconf.VALUE_STRING)

		# set up a default list if the list is not set
		if not ignore_list:
			ignore_list = DEFAULT_IGNORE

		return ignore_list


	def create_configure_dialog(self, dialog=None):
		# format the list as a comma separated string for display in the UI
		ignore_string = ', '.join(self.get_ignore_list())

		# set up the UI
		ui_file = self.find_file("artistprefix-config.ui")
		self.builder = gtk.Builder()
		self.builder.add_from_file(ui_file)

		self.builder.get_object("entry_ignore").set_text(ignore_string)

		dialog = self.builder.get_object("config_dialog")
		dialog.connect('response', self.config_dialog_response_cb)

		dialog.show_all()
		return dialog


	def config_dialog_response_cb(self, dialog, response):
		# grab the ignore list set by the user
		ignore_list = self.builder.get_object("entry_ignore").get_text().split(',')

		for i in range(len(ignore_list)):
			ignore_list[i] = ignore_list[i].strip()
			ignore_list[i] = ignore_list[i].capitalize()

		# write the list to gconf
		self.gconf.set_list(GCONF_KEYS['ignore'], gconf.VALUE_STRING, ignore_list)

		dialog.hide()

