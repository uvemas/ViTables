#!/usr/bin/env python
# -*- coding: utf-8 -*-


#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
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
Here is defined the QueriesManager class.

Classes:

* QueriesManager

Methods:


Functions:


Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import tables
import numpy

from PyQt4.QtCore import *

import vitables.utils


class QueriesManager(QThread):
    """This is the class in charge of threading the execution of queries.

    Making queries in a separated execution thread is an important improvement.
    It allows to query very large tables without freezing the rest of the
    application.

    The thread is implemented in a clever way that doesn't interfer with the
    lazy population of the tree of databases view: the query results table is
    stored under a hidden group of the temporary database until the query
    finishes. Then it is moved to the root node and becomes visible to the
    world. This way, while the query results table is partially filled it
    is not seen by the lazy population algorithm so it is not added to the
    tree of databases view and neither the user nor ViTables will try to read
    it. So no problems can occur trying to read a partially filled table.

    Also no more than one query can be made at the same time on a given table.
    This goal is achieved in a very simple way: tracking the tables currently
    being queried in a data structure (a dictionary at present).

    Note: what would happen if several very large tables are being run at the
    same time has not been (yet) checked. They could take all the available CPU
    of all available processors (so the application will be frozen until some
    query ended and released CPU). If there is a processor devoted to thread
    then the queries would take more time to finish but the rest of the application
    would not be affected (i.e. would not freeze).
    """
    def __init__(self, tmp_h5file, parent=None):
        """Setup the queries manager.

        The manager is in charge of:

        - keep a description of the last query made
        - automatically generate names for new queries
        - track the query names already in use
        - track the tables that are currently being queried

        The last query description has three components: the filepath of
        the file where the queried table lives, the nodepath of the queried
        table and the query condition.

        A query name is the name of the table where the query results are
        stored. By default it has the format "Filtered_TableUID" where UID
        is an integer automatically generated. User can customise the query
        name in the New Query dialog.

        :Parameter tmp_h5file: the file where the query results are stored
        """

        QThread.__init__(self, parent)

        self.tmp_h5file = tmp_h5file
        # Description of the last query made
        self.last_query = [None, None, None]
        # UID for automatically generating query names
        self.counter = 0
        # The list of query names currently in use
        self.ft_names = []
        # A mapping of tables being currently queried
        self.in_progress = {}


    def trackTable(self, tableID):
        """Add a new entry to the queries track system.

        :Parameter tableID: the ID of the table being tracked
        """
        self.in_progress[tableID] = True


    def untrackTable(self, tableID):
        """Remove an entry from the queries track system.

        :Parameter tableID: the ID of the table being released
        """
        del self.in_progress[tableID]



    def isTracked(self, tableID):
        """Find out if a table is being queried.

        :Parameter tableID: the ID of the table being checked
        """

        if self.in_progress.has_key(tableID):
            return True
        else:
            return False
    def query(self, tableID, table, query_description):
        """Start a new query.

        :Parameters:

        - `tableID`:the UID of the table to be queried
        - `table`: the table to be queried
        - `query_description`: the description of the query to be performed
        """

        self.tableID = tableID
        self.table = table
        self.query_description = query_description
        self.start()


    def run(self):
        """
        Query a table and add a the result to the temporary database.
        """

        table = self.table
        query_description = self.query_description
        tmp_h5file = self.tmp_h5file

        # Define shorthands
        (start, stop, step) = query_description[u'rows_range']
        name = query_description[u'ft_name']
        title = query_description[u'title']
        condition = query_description[u'condition']
        condvars = query_description[u'condvars']
        indices_field_name = query_description[u'indices_field_name']

        # If no slice is passed the best choice is to set the start, stop,
        # step arguments to None. It is due to the implementation of
        # readWhere
        if (start, stop, step) == (0, table.nrows, 1):
            (start, stop, step) = (None, None, None)

        try:
            src_dict = table.description._v_colObjects
            # Query the source table and build the result table
            if indices_field_name:
                            # Create the destination table: its first column
                            # will contain the indices of the rows selected in
                            # the source table so a new description dictionary
                            # is needed. Int64 values are necessary to keep full
                            # 64-bit indices
                            ft_dict = {indices_field_name.encode('utf_8'): \
                                tables.Int64Col(pos=-1)}
                            ft_dict.update(src_dict)
                            f_table = tmp_h5file.createTable(u'/_p_query_results', name, 
                                ft_dict, title)

                            # Get the array of rows that fullfill the condition
                            coordinates = table.getWhereList(condition, condvars, 
                                start=start, stop=stop, step=step)
                            selection = table.readCoordinates(coordinates)

                            # Fill the destination table
                            if selection.shape != (0, ):
                                dtype = f_table.read().dtype
                                # A one row array with the proper dtype will be used
                                # to fill the table
                                row_buffer = \
                                numpy.array([(coordinates[0], ) + \
                                    tuple(selection[0])], dtype=dtype)
                                f_table.append(row_buffer)
                                selection_index = 0
                                for row_index in coordinates[1:]:
                                    selection_index = selection_index + 1
                                    # Set the first field with the row index
                                    row_buffer[0][0] = row_index
                                    # The rest of fields are set using the query result
                                    for field_index in range(0, len(dtype) - 1):
                                        row_buffer[0][field_index+1] = \
                                            selection[selection_index][field_index]
                                    f_table.append(row_buffer)
                            # Move table to its final destination
                            tmp_h5file.moveNode(u'/_p_query_results/' + name, u'/',
                                newname=name, overwrite=True)
            else:
                            # Create the destination table
                            f_table = tmp_h5file.createTable(u'/_p_query_results', name, 
                                src_dict, title)
                            # Get the array of rows that fullfill the condition
                            selection = table.readWhere(condition, condvars, 
                                start=start, stop=stop, step=step)
                            # Fill the destination table
                            f_table.append(selection)
                            # Move table to its final destination
                            tmp_h5file.moveNode(u'/_p_query_results/' + name, u'/',
                                newname=name, overwrite=True)
        except:
            vitables.utils.formatExceptionInfo()
        else:
            f_table.flush()
            # Set some user attributes that define this filtered table
            asi = f_table.attrs
            asi.query_path = query_description[u'src_filepath']
            asi.query_table = query_description[u'src_path']
            asi.query_condition = f_table.title
            tmp_h5file.flush()
            # Update the list of names in use for filtered tables
            self.ft_names.append(query_description[u'ft_name'])
            self.last_query = [query_description[u'src_filepath'], 
                query_description[u'src_path'], 
                query_description[u'condition']]

        # Unlock the table for future queries
        self.untrackTable(self.tableID)
        self.emit(SIGNAL("queryFinished()"), )


