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
This module implements a controller for managing the queries.

The manager tracks the existing filtered tables and their names, launches the
Query dialog and executes the queries at low level (i.e. `PyTables` level).
It also keeps a description of the last executed query and tracks the tables
currently being queried, in order to ensure that no more than 1 query at a time
is executed on a given table.
"""

__docformat__ = 'restructuredtext'

import logging
import vitables.utils

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.queries.query as query
import vitables.queries.querydlg as querydlg


translate = QtWidgets.QApplication.translate

log = logging.getLogger(__name__)


def getTableInfo(table):
    """Retrieves table info required for querying it.

    :Parameter table: the `tables.Table` instance being queried.
    """
    info = {}
    info['nrows'] = table.nrows
    info['src_filepath'] = table._v_file.filename
    info['src_path'] = table._v_pathname
    info['name'] = table._v_name
    # Fields info: top level fields names, flat fields shapes and types
    info['col_names'] = frozenset(table.colnames)
    info['col_shapes'] = \
        dict((k, v.shape) for (k, v) in table.coldescrs.items())
    info['col_types'] = table.coltypes
    # Fields that can be queried
    info['condvars'] = {}
    info['valid_fields'] = []

    if info['nrows'] <= 0:
        log.info(
            translate('QueriesManager',
                      "Table {0} is empty. Nothing to query.",
                      'Info message for users').format(info['name']))
        return None

    # Find out the valid (i.e. searchable) fields and condition variables.
    # First discard nested fields.
    # Beware that order matters in binary operations that mix set instances
    # with frozensets: set & frozenset returns a set but frozenset & set
    # returns a frozenset
    valid_fields = set(info['col_shapes'].keys()).intersection(
        info['col_names'])
    # info['col_names'].intersection(info['col_shapes'].keys())

    # Then discard fields that aren't scalar and those that are complex
    for name in valid_fields.copy():
        if (info['col_shapes'][name] != ()) or \
           info['col_types'][name].count('complex'):
            valid_fields.remove(name)

    # Among the remaining fields, those whose names contain blanks
    # cannot be used in conditions unless they are mapped to
    # variables with valid names
    index = 0
    for name in valid_fields.copy():
        if name.count(' '):
            while ('col{0}'.format(index)) in valid_fields:
                index = index + 1
            info['condvars']['col{0}'.format(index)] = \
                table.cols._f_col(name)
            valid_fields.remove(name)
            valid_fields.add('col{0} ({1})'.format(index, name))
            index = index + 1
    info['valid_fields'] = valid_fields

    # If table has not columns suitable to be filtered does nothing
    if not info['valid_fields']:
        log.info(
            translate('QueriesManager',
                      """Table {0} has no columns suitable to be """
                      """queried. All columns are nested, multidimensional """
                      """or have a Complex data type.""",
                      'Info when trying to query a table').format(
                          info['name']))
        return None
    elif len(info['valid_fields']) != len(info['col_names']):
        # Log a message if non selectable fields exist
        log.warning(
            translate('QueriesManager',
                      """Some table columns contain multidimensional, """
                      """nested or Complex data. They cannot be queried so """
                      """are not included in the Column selector of the """
                      """query dialog.""", 'An informational note for users'))

    return info


class QueriesManager(QtCore.QObject):
    """This is the class in charge of the execution of queries.

    `PyTables` doesn't support threaded queries. So when several queries are
    requested to ``ViTables`` they will be executed sequentially.

    Also no more than one query can be made at the same time on a given table.
    This goal is achieved in a very simple way: tracking the tables currently
    being queried in a data structure (a dictionary at present).

    :Parameter parent: the parent of the `QueriesManager` object
    """

    def __init__(self, parent=None):
        """Setup the queries manager.

        The last query description has three components: the filepath of
        the file where the queried table lives, the nodepath of the queried
        table and the query condition.

        A query name is the name of the table where the query results are
        stored. By default it has the format "Filtered_TableUID" where UID
        is an integer automatically generated. User can customise the query
        name in the New Query dialog.
        """

        super(QueriesManager, self).__init__(parent)

        # Description of the last query made
        self.last_query = [None, None, None]
        # UID for automatically generating query names
        self.counter = 0
        # The list of query names currently in use
        self.ft_names = []

        self.vtapp = vitables.utils.getVTApp()
        self.vtgui = self.vtapp.gui
        self.dbt_view = self.vtgui.dbs_tree_view
        self.dbt_model = self.vtgui.dbs_tree_model

    def newQuery(self):
        """Process the query requests launched by users.
        """

        # The VTApp.updateQueryActions method ensures that the current node is
        # tied to a tables.Table instance so we can query it without
        # further checking
        current = self.dbt_view.currentIndex()
        node = self.dbt_model.nodeFromIndex(current)
        table_uid = node.as_record
        table = node.node

        table_info = getTableInfo(table)
        if table_info is None:
            return

        # Update the suggested name sufix
        self.counter = self.counter + 1
        query_description = self.getQueryInfo(table_info, table)
        if query_description is None:
            self.counter = self.counter - 1
            return

        # Update the list of names in use for filtered tables
        self.ft_names.append(query_description['ft_name'])
        self.last_query = [query_description['src_filepath'],
                           query_description['src_path'],
                           query_description['condition']]

        # Run the query
        tmp_h5file = self.dbt_model.tmp_dbdoc.h5file
        new_query = query.Query(tmp_h5file, table_uid, table,
                                query_description)
        new_query.query_completed.connect(self.addQueryResult)
        QtWidgets.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
        new_query.run()

    def getQueryInfo(self, info, table):
        """Retrieves useful info about the query.

        :Parameters:

        - `info`: dictionary with info about the queried table
        - `table`: the tables.Table instance being queried
        """

        # Information about table
        # Setup the initial condition
        last_query = self.last_query
        if (last_query[0], last_query[1]) == (info['src_filepath'],
                                              info['src_path']):
            initial_condition = last_query[2]
        else:
            initial_condition = ''

        # GET THE QUERY COMPONENTS
        # Get a complete query description from user input: condition to
        # be applied, involved range of rows, name of the
        # filtered table and name of the column of returned indices
        query_dlg = querydlg.QueryDlg(info, self.ft_names,
                                      self.counter, initial_condition, table)
        try:
            query_dlg.exec_()
        finally:
            query_description = dict(query_dlg.query_info)
            del query_dlg
            QtWidgets.qApp.processEvents()

        if not query_description['condition']:
            return None

        # SET THE TITLE OF THE RESULT TABLE
        title = query_description['condition']
        for name in info['valid_fields']:
            # Valid fields can have the format 'fieldname' or
            # 'varname (name with blanks)' so a single blank shouldn't
            # be used as separator
            components = name.split(' (')
            if len(components) > 1:
                fieldname = '({0}'.format(components[-1])
                title = title.replace(components[0], fieldname)
        query_description['title'] = title

        return query_description

    def deleteAllQueries(self):
        """
        Delete all nodes under the `Query results` node of the databases tree.
        """

        title = translate('QueriesManager', 'Cleaning the Query results file',
                          'Caption of the QueryDeleteAll dialog')
        text = translate('QueriesManager', ('\n\nYou are about to delete all '
                                            'nodes under Query results\n\n'),
                         'Ask for confirmation')
        itext = ''
        dtext = ''
        buttons = {
            'Delete': (translate('QueriesManager', 'Delete', 'Button text'),
                       QtWidgets.QMessageBox.YesRole),
            'Cancel': (translate('QueriesManager', 'Cancel', 'Button text'),
                       QtWidgets.QMessageBox.NoRole)}
        # Ask for confirmation
        answer = vitables.utils.questionBox(title, text, itext, dtext, buttons)
        if answer == 'Cancel':
            return

        # Remove every filtered table from the tree of databases model/view
        model_rows = self.dbt_model.rowCount(QtCore.QModelIndex())
        tmp_index = self.dbt_model.index(model_rows - 1, 0,
                                         QtCore.QModelIndex())
        rows_range = list(
            range(0, self.dbt_model.rowCount(tmp_index)).__reversed__())
        for row in rows_range:
            index = self.dbt_model.index(row, 0, tmp_index)
            self.vtapp.nodeDelete(index, force=True)

        # Reset the queries manager
        self.counter = 0
        self.ft_names = []

    def addQueryResult(self, completed, table_uid):
        """Update the GUI once the query has finished.

        Add the result of the query to the tree of databases view and open
        the new filtered table.

        :Parameters:

        - `completed`: whether the query has been succesful or not
        - `table_uid`: the UID of the table just queried
        """

        QtWidgets.qApp.restoreOverrideCursor()
        if not completed:
            log.error(translate('QueriesManager',
                                'Query on table {0} failed!',
                                'Warning log message about a failed '
                                'query').format(table_uid))
            return

        # Update temporary database view i.e. call lazyAddChildren
        model_rows = self.dbt_model.rowCount(QtCore.QModelIndex())
        tmp_index = self.dbt_model.index(model_rows - 1, 0,
                                         QtCore.QModelIndex())
        self.dbt_model.lazyAddChildren(tmp_index)

        # The new filtered table is inserted in first position under
        # the Query results node and opened
        index = self.dbt_model.index(0, 0, tmp_index)
        self.vtapp.nodeOpen(index)
