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

class ArtistPrefix(rb.Plugin):
	def __init__(self):
		rb.Plugin.__init__(self)

	def on_artist_prefix_query(self, model, path, iter):
		# note: path and iter are effectively useless as a gtkTree doesn't populate the row on row-insert
		# see GTK documentation for row-inserted signal for more info
		# so we simple iterate over the model instead
		for row in model:
			entry = row[0]
			artist_sort = re.sub('^The\s*','',self.db.entry_get(entry, rhythmdb.PROP_ARTIST),1,re.I)
			self.db.set(entry,rhythmdb.PROP_ARTIST_SORTNAME,artist_sort)
			self.db.commit()
			model.remove_entry(entry)

	def activate (self, shell):
		self.shell = shell

		self.db = shell.props.db
		query = self.db.query_new()
		self.db.query_append(query,[rhythmdb.QUERY_PROP_PREFIX,rhythmdb.PROP_ARTIST,'The'],
                                           [rhythmdb.QUERY_PROP_EQUALS,rhythmdb.PROP_ARTIST_SORTNAME,''])
		self.artist_prefix_query = self.db.query_model_new(query)
		self.db.do_full_query_async_parsed(self.artist_prefix_query, query)
		self.artist_prefix_query.connect('row-inserted',self.on_artist_prefix_query)

	def deactivate(self, shell):
		del self.artist_prefix_query

