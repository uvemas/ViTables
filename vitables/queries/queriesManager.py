# -*- coding: utf-8 -*-
#!/usr/bin/env python

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
_context = 'QueriesManager'

import sets

import tables
import numpy

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import vitables.utils
import queryDlg

class QueriesManager(QObject):
    """This is the class in charge of threading the execution of queries.

    PyTables doesn't support threaded queries. So when several queries are
    requested to ViTables they will be executed sequentially. However the
    queries will not be executed in the ViTables main thread but in a
    secondary one. This way we ensure that queries (that are potentially
    long-running operations) will not freeze the user interface and ViTables
    will remain usable while queries are running (unless the queried table is
    so large or the query so complex that the query it eats all the available
    computer resources, CPU and memory).

    Also no more than one query can be made at the same time on a given table.
    This goal is achieved in a very simple way: tracking the tables currently
    being queried in a data structure (a dictionary at present).
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

        QObject.__init__(self, parent)

        self.mutex = QMutex()
        self.tmp_h5file = tmp_h5file
        # Description of the last query made
        self.last_query = [None, None, None]
        # UID for automatically generating query names
        self.counter = 0
        # The list of query names currently in use
        self.ft_names = []
        # A mapping of tables being currently queried
        self.in_progress = {}

        self.vtapp = vitables.utils.getVTApp()
        self.dbt_view = self.vtapp.dbs_tree_view
        self.dbt_model = self.vtapp.dbs_tree_model


    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate(_context, source, comment))


    def trackTable(self, tableID, thread=None):
        """Add a new entry to the queries track system.

        :Parameters:

        - `tableID`: the UID of the table being queried
        - `thread`: the QThread where the query will execute
        """
        self.in_progress[tableID] = thread


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


    def getTableInfo(self, table):
        """Retrieves table info required for querying it.

        :Parameter table: the tables.Table instance being queried.
        """
        info = {}
        info[u'nrows'] = table.nrows
        info[u'src_filepath'] = unicode(table._v_file.filename)
        info[u'src_path'] = table._v_pathname
        info[u'name'] = table._v_name
        # Fields info: top level fields names, flat fields shapes and types
        info[u'col_names'] = sets.Set(table.colnames)
        info[u'col_shapes'] = \
            dict((k, v.shape) for (k, v) in table.coldescrs.iteritems())
        info[u'col_types'] = table.coltypes
        # Fields that can be queried
        info[u'condvars'] = {}
        info[u'valid_fields'] = []

        if info[u'nrows'] <= 0:
            print self.__tr("""Caveat: table %s is empty. Nothing to query.""",
                'Warning message for users') % info[u'name']
            return None

        # The searchable fields and condition variables
        # First discard nested fields
        valid_fields = \
        info[u'col_names'].intersection(info[u'col_shapes'].keys())

        # Then discard fields that aren't scalar and those that are complex
        for name in valid_fields.copy():
            if (info[u'col_shapes'][name] != ()) or \
            info[u'col_types'][name].count(u'complex'):
                valid_fields.remove(name)

        # Among the remaining fields, those whose names contain blanks
        # cannot be used in conditions unless they are mapped to
        # variables with valid names
        index = 0
        for name in valid_fields.copy():
            if name.count(' '):
                while (u'col%s' % index) in valid_fields:
                    index = index + 1
                info[u'condvars'][u'col%s' % index] = \
                    table.cols._f_col(name)
                valid_fields.remove(name)
                valid_fields.add(u'col%s (%s)' % (index, name))
                index = index + 1
        info[u'valid_fields'] = valid_fields

        # If table has not columns suitable to be filtered does nothing
        if not info[u'valid_fields']:
            print self.__tr("""\nError: table %s has no """
            """columns suitable to be queried. All columns are nested, """
            """multidimensional or have a Complex data type.""",
            'An error when trying to query a table') % info['name']
            return None
        elif len(info[u'valid_fields']) != len(info[u'col_names']):
        # Log a message if non selectable fields exist
            print self.__tr("""\nWarning: some table columns contain """
               """nested, multidimensional or Complex data. They """
               """cannot be queried so are not included in the Column"""
               """ selector of the query dialog.""",
               'An informational note for users')

        return info


    def getQueryInfo(self, info, table):
        """Retrieves useful info about the query.

        :Parameters:

        - `info`: dictionary with info about the queried table
        - `table`: the tables.Table instance being queried
        """

        # Information about table
        # Setup the initial condition
        last_query = self.last_query
        if (last_query[0], last_query[1]) == \
        (info[u'src_filepath'], info[u'src_path']):
            initial_condition = last_query[2]
        else:
            initial_condition = ''

        # GET THE QUERY COMPONENTS
        # Get a complete query description from user input: condition to
        # be applied, involved range of rows, name of the
        # filtered table and name of the column of returned indices
        query = queryDlg.QueryDlg(info, self.ft_names, 
            self.counter, initial_condition, table)
        try:
            query.exec_()
        finally:
            query_description = dict(query.query_info)
            del query

        if not query_description[u'condition']:
            return None

        # SET THE TITLE OF THE RESULT TABLE
        title = query_description[u'condition']
        for name in info[u'valid_fields']:
            # Valid fields can have the format 'fieldname' or 
            # 'varname (name with blanks)' so a single blank shouldn't
            # be used as separator
            components = name.split(u' (')
            if len(components) > 1:
                fieldname = u'(%s' % components[-1]
                title = title.replace(components[0], fieldname)
        query_description[u'title'] = title

        return query_description


    def newQuery(self):
        """Proces the query requests launched by users.
        """

        # The VTApp.updateQueryActions method ensures that the current node is
        # tied to a tables.Table instance so we can query it without
        # further checking
        current = self.dbt_view.currentIndex()
        node = self.dbt_model.nodeFromIndex(current)
        tableID = node.as_record
        table = node.node

        if self.isTracked(tableID):
            print self.__tr("A query is already in progress for this table!", 
                'Console message from slotQueryNew method')
            return

        table_info = self.getTableInfo(table)
        if table_info is None:
            return

        # Update the suggested name sufix
        self.counter = self.counter + 1
        query_description = self.getQueryInfo(table_info, table)
        if query_description is None:
            self.counter = self.counter - 1
            return

        # Update the list of names in use for filtered tables
        self.ft_names.append(query_description[u'ft_name'])
        self.last_query = [query_description[u'src_filepath'], 
            query_description[u'src_path'], query_description[u'condition']]

        # Find out the subwindow tied to the selected node and disable it
    #    for subwindow in self.vtapp.workspace.subWindowList():
    #        if subwindow.leaf == node:
    #            subwindow.setEnabled(False)

        # Run the query in a secondary thread
        self.trackTable(tableID, 
            Query(tableID, table, query_description, parent=self))

        self.connect(self.in_progress[tableID], SIGNAL("finished()"), 
            self.in_progress[tableID], SLOT("deleteLater()"))

        self.in_progress[tableID].start()


    def deleteAllQueries(self):
        """Delete all nodes from the query results tree."""

        del_dlg = QMessageBox.question(self.vtapp,
            self.__tr('Deleting all queries',
            'Caption of the QueryDeleteAll dialog'),
            self.__tr("""\n\nYou are about to delete all nodes """
                """under Query results\n\n""", 'Ask for confirmation'),
            QMessageBox.Yes|QMessageBox.Default,
            QMessageBox.No|QMessageBox.Escape)

        # OK returns Accept, Cancel returns Reject
        if del_dlg == QMessageBox.No:
            return

        # Remove every filtered table from the tree of databases model/view
        model_rows = self.dbt_model.rowCount(QModelIndex())
        tmp_index = self.dbt_model.index(model_rows - 1, 0, 
            QModelIndex())
        rows_range = range(0, self.dbt_model.rowCount(tmp_index))
        rows_range.reverse()
        for row in rows_range:
            index = self.dbt_model.index(row, 0, tmp_index)
            self.vtapp.slotNodeDelete(index, force=True)

        # Reset the queries manager
        self.counter = 0
        self.ft_names = []


    def addQueryResult(self, tableID):
        """Update the GUI once the query has finished.

        Add the result of the query to the tree of databases view and open
        the new filtered table.

        :Parameter tableID: the UID of the table just queried
        """

        # Update temporary database view i.e. call lazyAddChildren
        model_rows = self.dbt_model.rowCount(QModelIndex())
        tmp_index = self.dbt_model.index(model_rows - 1, 0, 
            QModelIndex())
        self.dbt_model.lazyAddChildren(tmp_index)
        # The new filtered table is inserted in first position under
        # the Query results node and opened
        index = self.dbt_model.index(0, 0, tmp_index)
        self.vtapp.slotNodeOpen(index)

        self.untrackTable(tableID)


class Query(QThread):
    """Class implementing a tables.Table query.

    Queries are sequentially executed in a secondary thread so the GUI will
    not freeze up while the query (a potentially long-running operation) is
    taking place.

    The thread is implemented in a clever way that doesn't interfer with the
    lazy population of the tree of databases view: the query results table is
    stored under a hidden group of the temporary database until the query
    finishes. Then it is moved to the root node and becomes visible to the
    world. This way, while the query results table is partially filled it
    is not seen by the lazy population algorithm so it is not added to the
    tree of databases view and neither the user nor ViTables will try to read
    it. So no problems can occur trying to read a partially filled table.
    """


    def __init__(self, tableID, table, qdescr, parent=None):
        """Initialises the thread.

        :Parameters:

        - `tableID`: UID of the tables.Table instance being queried
        - `table`: tables.Table instance being queried
        - `qdescr`: dictionary description of the query
        - `parent`: the queries manager
        """

        QThread.__init__(self, parent)

        self.connect(self, SIGNAL("queryFinished"), parent.addQueryResult)
        self.qmgr = parent
        self.mutex = parent.mutex
        self.tableID = tableID
        self.table = table
        self.query_description = qdescr



    def flushTable(self, ftable):
        """Flush the filtered table and setup some user attributes.

        :Parameters:

        - `ftable`: the filtered table being flushed
        """

        ftable.flush()
        # Set some user attributes that define this filtered table
        asi = ftable.attrs
        asi.query_path = self.query_description[u'src_filepath']
        asi.query_table = self.query_description[u'src_path']
        asi.query_condition = self.query_description[u'title']


    def run(self):
        """
        Query a table and add a the result to the temporary database.
        """

        locker = QMutexLocker(self.mutex)
        table = self.table
        tmp_h5file = self.qmgr.tmp_h5file

        # Define shorthands
        (start, stop, step) = self.query_description[u'rows_range']
        name = self.query_description[u'ft_name']
        title = self.query_description[u'title']
        condition = self.query_description[u'condition']
        condvars = self.query_description[u'condvars']
        indices_field_name = self.query_description[u'indices_field_name']

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
                self.flushTable(f_table)
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
                self.flushTable(f_table)
                tmp_h5file.moveNode(u'/_p_query_results/' + name, u'/',
                    newname=name, overwrite=True)
        except:
            vitables.utils.formatExceptionInfo()
        else:
            tmp_h5file.flush()
            self.emit(SIGNAL("queryFinished"), self.tableID)
