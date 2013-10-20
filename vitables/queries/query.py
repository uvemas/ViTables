#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Author:  Vicent Mas - vmas@vitables.org

"""
This module executes `tables.Table` queries at low level.

It collects information from the `New Query` dialog, processes it and then
executes the query.
"""

__docformat__ = 'restructuredtext'

import tables
import numpy

from PyQt4 import QtCore
from PyQt4 import QtGui

import vitables.utils

translate = QtGui.QApplication.translate


class Query(QtCore.QObject):
    """Class implementing a tables.Table query.

    Ideally queries SHOULD be sequentially executed in a secondary thread for
    keeping the GUI responsive (i.e. not frozen) while a query (a potentially
    long-running operation) is taking place. Unfortunately this goal has
    proven difficult to achieve because `PyTables` is not thread-safe. So one
    more task to the TO DO list :-)

    The query is implemented in a clever way that doesn't interfer with the
    lazy population of the tree of databases view: the query results table is
    stored under a hidden group of the temporary database until the query
    finishes. Then it is moved to the root node and becomes visible to the
    world. This way, while the query results table is partially filled it
    is not seen by the lazy population algorithm so it is not added to the
    tree of databases view and neither the user nor ViTables will try to read
    it. So no problems can occur trying to read a partially filled table.

    :Parameters:

    - `table_uid`: UID of the tables.Table instance being queried
    - `table`: the table being queried
    - `qdescr`: dictionary description of the query
    """


    query_completed = QtCore.pyqtSignal(bool, unicode, name="queryCompleted")


    def __init__(self, tmp_h5file, table_uid, table, qdescr):
        """Initialises the query."""

        super(Query, self).__init__()

        self.completed = False
        self.tmp_h5file = tmp_h5file
        self.table_uid = table_uid
        self.table = table
        self.qdescr = qdescr


    def run(self):
        """
        Query a table and add a the result to the temporary database.
        """

        self.queryTable()
        self.query_completed.emit(self.completed, self.table_uid)


    def flushTable(self, ftable):
        """Flush the filtered table and setup some user attributes.

        :Parameters:

        - `ftable`: the filtered table being flushed
        """

        ftable.flush()
        # Set some user attributes that define this filtered table
        asi = ftable.attrs
        asi.query_path = self.qdescr[u'src_filepath']
        asi.query_table = self.qdescr[u'src_path']
        asi.query_condition = self.qdescr[u'title']


    def queryWithIndex(self, src_dict):
        """Do the query (`PyTables` level).
        """

        # The query range is made of numpy scalars with dtype int64
        (start, stop, step) = self.qdescr[u'rows_range']
        chunk_size = 10000
        div = numpy.divide(stop - start, chunk_size)

        # Create the destination table: its first column will contain
        # the indices of the rows selected in the source table so a new
        # description dictionary is needed. Int64 values are necessary
        # to keep full 64-bit indices
        ft_dict = \
            {self.qdescr[u'indices_field_name'].encode('utf_8'): \
            tables.Int64Col(pos=-1)}
        ft_dict.update(src_dict)
        f_table = self.tmp_h5file.createTable(\
            u'/_p_query_results',
            self.qdescr[u'ft_name'],
            ft_dict,
            self.qdescr[u'title'])

        # Get the array of rows that fulfill the condition
        # Selection is done in several steps. It saves a *huge*
        # amount of memory when querying large tables
        for i in numpy.arange(0, div+1):
            QtGui.qApp.processEvents()
            lstart = start + chunk_size*i
            if lstart > stop:
                lstart = stop
            lstop = lstart + chunk_size
            if lstop > stop:
                lstop = stop
            coordinates = self.table.getWhereList(\
                self.qdescr[u'condition'],
                self.qdescr[u'condvars'],
                start=lstart, stop=lstop, step=step)
            selection = self.table.readCoordinates(coordinates)
            if selection.shape == (0, ):
                continue

            coord_dtype = numpy.dtype(\
                [(str(self.qdescr[u'indices_field_name']), '<i8')])
            new_dtype = numpy.dtype(\
                coord_dtype.descr + selection.dtype.descr)

            new_buffer = numpy.empty(selection.shape, dtype=new_dtype)
            for field in selection.dtype.fields:
                new_buffer[field] = selection[field]
            new_buffer[str(self.qdescr[u'indices_field_name'])] = \
                coordinates
            f_table.append(new_buffer)
            self.flushTable(f_table)

        # Move the intermediate table to its final destination
        self.tmp_h5file.moveNode(\
            u'/_p_query_results/' + self.qdescr[u'ft_name'],
            u'/', newname=self.qdescr[u'ft_name'],
            overwrite=True)
        self.completed = True


    def queryWithNoIndex(self, src_dict):
        """Do the query (`PyTables` level).
        """

        # The query range is made of numpy scalars with dtype int64
        (start, stop, step) = self.qdescr[u'rows_range']
        chunk_size = 10000
        div = numpy.divide(stop - start, chunk_size)

        # Create the destination table
        f_table = self.tmp_h5file.createTable(\
            u'/_p_query_results',
            self.qdescr[u'ft_name'],
            src_dict,
            self.qdescr[u'title'])

        # Get the array of rows that fulfill the condition
        # Selection is done in several steps. It saves a *huge*
        # amount of memory when querying large tables
        for i in numpy.arange(0, div+1):
            QtGui.qApp.processEvents()
            lstart = start + chunk_size*i
            if lstart > stop:
                lstart = stop
            lstop = lstart + chunk_size
            if lstop > stop:
                lstop = stop
            selection = self.table.readWhere(\
                self.qdescr[u'condition'],
                self.qdescr[u'condvars'],
                start=lstart, stop=lstop, step=step)
            f_table.append(selection)
            self.flushTable(f_table)

        # Move the intermediate table to its final destination
        self.tmp_h5file.moveNode(\
            u'/_p_query_results/' + self.qdescr[u'ft_name'],
            u'/', newname=self.qdescr[u'ft_name'],
            overwrite=True)
        self.completed = True


    def queryTable(self):
        """Do the query (`PyTables` level).
        """

        try:
            src_dict = self.table.description._v_colObjects
            # Add an `indexes` column to the result table
            if self.qdescr[u'indices_field_name']:
                self.queryWithIndex(src_dict)
            # Do no add an `indexes` column to the result table
            else:
                self.queryWithNoIndex(src_dict)
        except KeyError:
            vitables.utils.formatExceptionInfo()
            self.tmp_h5file.removeNode(\
                u'/_p_query_results/' + self.qdescr[u'ft_name'])
        else:
            self.tmp_h5file.flush()
