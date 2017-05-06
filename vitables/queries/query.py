#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
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

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.utils

translate = QtWidgets.QApplication.translate


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


    query_completed = QtCore.Signal(bool, str, name="queryCompleted")


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
        asi.query_path = self.qdescr['src_filepath']
        asi.query_table = self.qdescr['src_path']
        asi.query_condition = self.qdescr['title']


    def queryWithIndex(self, src_dict):
        """Do the query (`PyTables` level).
        """

        # The query range is made of numpy scalars with dtype int64
        (start, stop, step) = self.qdescr['rows_range']
        chunk_size = 10000
        div = int((stop - start) // chunk_size)

        # Create the destination table: its first column will contain
        # the indices of the rows selected in the source table so a new
        # description dictionary is needed. Int64 values are necessary
        # to keep full 64-bit indices
        ft_dict = {self.qdescr['indices_field_name']: tables.Int64Col(pos=-1)}
        ft_dict.update(src_dict)
        f_table = self.tmp_h5file.create_table(
            '/_p_query_results',
            self.qdescr['ft_name'],
            ft_dict,
            self.qdescr['title'])

        # Get the array of rows that fulfill the condition
        # Selection is done in several steps. It saves a *huge*
        # amount of memory when querying large tables
        for i in numpy.arange(0, div+1):
            QtWidgets.qApp.processEvents()
            lstart = start + chunk_size*i
            if lstart > stop:
                lstart = stop
            lstop = lstart + chunk_size
            if lstop > stop:
                lstop = stop
            coordinates = self.table.get_where_list(
                self.qdescr['condition'],
                self.qdescr['condvars'],
                start=lstart, stop=lstop, step=step)
            selection = self.table.read_coordinates(coordinates)
            if selection.shape == (0, ):
                continue

            coord_dtype = numpy.dtype(
                [(str(self.qdescr['indices_field_name']), '<i8')])
            new_dtype = numpy.dtype(
                coord_dtype.descr + selection.dtype.descr)

            new_buffer = numpy.empty(selection.shape, dtype=new_dtype)
            for field in selection.dtype.fields:
                new_buffer[field] = selection[field]
            new_buffer[str(self.qdescr['indices_field_name'])] = \
                coordinates
            f_table.append(new_buffer)
            self.flushTable(f_table)

        # Move the intermediate table to its final destination
        self.tmp_h5file.move_node(
            '/_p_query_results/' + self.qdescr['ft_name'],
            '/', newname=self.qdescr['ft_name'],
            overwrite=True)
        self.completed = True


    def queryWithNoIndex(self, src_dict):
        """Do the query (`PyTables` level).
        """

        # The query range is made of numpy scalars with dtype int64
        (start, stop, step) = self.qdescr['rows_range']
        chunk_size = 10000
        div = int((stop - start) // chunk_size)

        # Create the destination table
        f_table = self.tmp_h5file.create_table(
            '/_p_query_results',
            self.qdescr['ft_name'],
            src_dict,
            self.qdescr['title'])

        # Get the array of rows that fulfill the condition
        # Selection is done in several steps. It saves a *huge*
        # amount of memory when querying large tables
        for i in numpy.arange(0, div+1):
            QtWidgets.qApp.processEvents()
            lstart = start + chunk_size*i
            if lstart > stop:
                lstart = stop
            lstop = lstart + chunk_size
            if lstop > stop:
                lstop = stop
            selection = self.table.read_where(
                self.qdescr['condition'],
                self.qdescr['condvars'],
                start=lstart, stop=lstop, step=step)
            f_table.append(selection)
            self.flushTable(f_table)

        # Move the intermediate table to its final destination
        self.tmp_h5file.move_node(
            '/_p_query_results/' + self.qdescr['ft_name'],
            '/', newname=self.qdescr['ft_name'],
            overwrite=True)
        self.completed = True


    def queryTable(self):
        """Do the query (`PyTables` level).
        """

        try:
            src_dict = self.table.description._v_colobjects
            # Add an `indexes` column to the result table
            if self.qdescr['indices_field_name']:
                self.queryWithIndex(src_dict)
            # Do no add an `indexes` column to the result table
            else:
                self.queryWithNoIndex(src_dict)
        except KeyError:
            vitables.utils.formatExceptionInfo()
            self.tmp_h5file.remove_node(
                '/_p_query_results/' + self.qdescr['ft_name'])
        else:
            self.tmp_h5file.flush()
