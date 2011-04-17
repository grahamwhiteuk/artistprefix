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
import webbrowser

DEFAULT_IGNORE = ['The','El','La','Los','Las','Le','Les']

GCONF_KEYS = {
	'ignore': '/apps/rhythmbox/plugins/artistprefix/ignore',
	'overwrite': '/apps/rhythmbox/plugins/artistprefix/overwrite'
}

class ArtistPrefix(rb.Plugin):
	# __init__()
	# Constructor
	def __init__(self):
		rb.Plugin.__init__(self)

	# activate(shell)
	# Required RB plugin function to activate the plugin
	# Parameters:
	#   shell - a reference to the RB shell object
	def activate (self, shell):
		self.gconf = gconf.client_get_default()
		self.db = shell.props.db
		self.build_query(self.gconf.get_list(GCONF_KEYS['ignore'], gconf.VALUE_STRING))


	# deactivate(shell)
	# Required RB plugin function to deactivate the plugin
	# Parameters:
	#   shell - a reference to the RB shell object
	def deactivate(self, shell):
		del self.artist_prefix_query
		del self.db
		del self.gconf

	# build_query(ignore_list)
	# Builds and runs a query against the RB database returning entries as specified in the user configuration
	# Parameters:
	#   ignore_list - an array of strings to search for in the start of each artists name
	def build_query(self, ignore_list):
		# if no ignore list is set in gconf then don't run the query
		# ensures user selects the prefixes they wish to ignore before running the plugin
		if ignore_list is None:
			return

		query = self.db.query_new()

		for i, ignore in enumerate(ignore_list):
			# append query from the ignore list ANDed with a blank sortname
			self.db.query_append(query,[rhythmdb.QUERY_PROP_PREFIX,rhythmdb.PROP_ARTIST,ignore + ' '])

			if not self.gconf.get_bool(GCONF_KEYS['overwrite']):
				self.db.query_append(query,[rhythmdb.QUERY_PROP_EQUALS,rhythmdb.PROP_ARTIST_SORTNAME,''])

			if (i != len(ignore_list)-1):
				# if we've got more queries coming add a disjunction (which does a logical OR with the next query)
				self.db.query_append(query, [rhythmdb.QUERY_DISJUNCTION])

		self.artist_prefix_query = self.db.query_model_new(query)
		self.db.do_full_query_async_parsed(self.artist_prefix_query, query)
		self.artist_prefix_query.connect('row-inserted',self.on_artist_prefix_query)


	# on_artist_prefix_query(model, path, iter)
	# Called automatically every time the DB query finds a match
	# Parameters:
	#   model - a reference to the RhythmDBQueryModel model
	#   path  - a gtk.TreePath to the entry found
	#   iter  - a gtk.TreeIter pointing at path
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


	# create_configure_dialog(shell)
	# Standard RB function name to display the configure dialog box
	# Parameters:
	#   dialog - a reference to a dialog object
	# Returns:
	#   gtk.Dialog
	def create_configure_dialog(self, dialog=None):
		ignore_list = self.gconf.get_list(GCONF_KEYS['ignore'], gconf.VALUE_STRING)

		# set up a default list if the list is not set
		if not ignore_list:
			ignore_list = DEFAULT_IGNORE

		# format the list as a comma separated string for display in the UI
		ignore_string = ', '.join(ignore_list)

		# set up the UI
		ui_file = self.find_file("artistprefix-config.ui")
		self.builder = gtk.Builder()
		self.builder.add_from_file(ui_file)

		self.builder.get_object("entryIgnore").set_text(ignore_string)
		self.builder.get_object("cb_overwrite").set_active(self.gconf.get_bool(GCONF_KEYS['overwrite']))

		dialog = self.builder.get_object("config_dialog")
		dialog.connect('response', self.config_dialog_response_cb)

		return dialog


	# config_dialog_response_cb(dialog, response)
	# Called when a user clicks a button in the configure dialog box
	# Parameters:
	#   dialog   - a reference to the dialog
	#   response - the response number of the button clicked
	def config_dialog_response_cb(self, dialog, response):
		# OK buton
		if response is 1:
			# grab the ignore list set by the user
			ignore_list = self.builder.get_object("entryIgnore").get_text().split(',')
	
			for i in range(len(ignore_list)):
				ignore_list[i] = ignore_list[i].strip()
				ignore_list[i] = ignore_list[i].capitalize()

			# write the list to gconf
			self.gconf.set_list(GCONF_KEYS['ignore'], gconf.VALUE_STRING, ignore_list)
			
			# write the overwrite config to gconf
			self.gconf.set_bool(GCONF_KEYS['overwrite'], self.builder.get_object("cb_overwrite").get_active())

			# run the query
			self.build_query(ignore_list)
	
		# not Help button	
		if response is not 3:
			dialog.hide()
		else:
			webbrowser.open_new('http://code.google.com/p/artistprefix/')

