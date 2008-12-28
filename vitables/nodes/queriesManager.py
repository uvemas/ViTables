# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008 Vicent Mas. All rights reserved
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
#
#       $Source$
#       $Id: queriesManager.py 1083 2008-11-04 16:41:02Z vmas $
#
########################################################################

"""
Here is defined the QueriesManager class.

Classes:

* QueriesManager

Methods:

* __init__(self, tmp_h5file)
* __tr(self,  source, comment=None)
* getQueryInfo(self, table)
* queryTable(self, table, query_info, title)

Functions:


Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import sets

import tables.exceptions

import numpy

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.utils
import vitables.vtWidgets.queryDlg as queryDlg

class QueriesManager:

    def __init__(self, tmp_h5file):
        """Setup the queries manager.

        :Parameter tmp_h5file: the temporary database.
        """

        self.last_query = [None, None, None]
        self.counter = 0
        self.ft_names = []
        self.tmp_h5file = tmp_h5file


    def __tr(self,  source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate('QueriesManager', source, 
                                            comment).toUtf8(), 'utf_8')


    def getQueryInfo(self, table):
        """Retrieves useful info about the query.

        :Parameter table: the tables.Table instance being queried.
        """

        # Information about table
        info = {}
        info['nrows'] = table.nrows
        info['src_filepath'] = table._v_file.filename
        info['src_path'] = table._v_pathname
        info['name'] = table._v_name
        # Fields info: top level fields names, flat fields shapes and types
        info['col_names'] = sets.Set(table.colnames)
        info['col_shapes'] = \
            dict((k, v.shape) for (k, v) in table.coldescrs.iteritems())
        info['col_types'] = table.coltypes
        # Fields that can be queried
        info['condvars'] = {}
        info['valid_fields'] = []

        if info['nrows'] <= 0:
            print self.__tr("""Caveat: table %s is empty. Nothing to query.""",
                'Warning message for users') % info['name']
            return None

        # The searchable fields and condition variables
        # First discard nested fields
        valid_fields = \
        info['col_names'].intersection(info['col_shapes'].keys())

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
                while ('col%s' % index) in valid_fields:
                    index = index + 1
                info['condvars']['col%s' % index] = \
                    table.cols._f_col(name)
                valid_fields.remove(name)
                valid_fields.add('col%s (%s)' % (index, name))
                index = index + 1
        info['valid_fields'] = valid_fields

        # If table has not columns suitable to be filtered does nothing
        if not info['valid_fields']:
            print self.__tr("""\nError: table %s has no """
            """columns suitable to be queried. All columns are nested, """
            """multidimensional or have a Complex data type.""",
            'An error when trying to query a table') % info['name']
            return None
        elif len(info['valid_fields']) != len(info['col_names']):
        # Log a message if non selectable fields exist
            print self.__tr("""\nWarning: some table columns contain """
               """nested, multidimensional or Complex data. They """
               """cannot be queried so are not included in the Column"""
               """ selector of the query dialog.""",
               'An informational note for users')

        # Setup the initial condition
        if (self.last_query[0], self.last_query[1]) == \
        (info['src_filepath'], info['src_path']):
            initial_condition = self.last_query[2]
        else:
            initial_condition = ''

        # GET THE QUERY COMPONENTS
        # Update the sufix of the suggested name to ensure that it is not in use
        self.counter = self.counter + 1
        # Retrieve information about the query: condition to
        # be applied, involved range of rows, name of the
        # filtered table and name of the column of returned indices
        query = queryDlg.QueryDlg(info, self.ft_names, 
            self.counter, initial_condition, table)
        try:
            query.exec_()
            # Cancel clicked
            if query.result() == QtGui.QDialog.Rejected:
                self.counter = self.counter - 1 # Restore the counter value
        finally:
            query_info = dict(query.query_info)
            del query

        if not query_info['condition']:
            return None

        # SET THE TITLE OF THE RESULT TABLE
        title = query_info['condition']
        for name in info['valid_fields']:
            # Valid fields can have the format 'fieldname' or 
            # 'varname (name with blanks)' so a single blank shouldn't
            # be used as separator
            components = name.split(' (')
            if len(components) > 1:
                fieldname = '(%s' % components[-1]
                title = title.replace(components[0], fieldname)

        return query_info, title


    def queryTable(self, table, query_info, title):
        """
        Query a table and add a the result to the temporary database.

        :Parameters:

        - `table`: the tables.Table instance being queried
        - `query_info`: a dictionary with information about the query
        - `title`: the title of the result table
        """

        # QUERY THE TABLE
        QtGui.qApp.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:

            # Define shorthands
            (start, stop, step) = query_info['rows_range']
            name = query_info['ft_name']
            condition = query_info['condition']
            condvars = query_info['condvars']
            indices_field_name = query_info['indices_field_name']

            # If no slice is passed the best choice is to set the start, stop,
            # step arguments to None. It is due to the implementation of
            # readWhere
            if (start,  stop, step) == (0, table.nrows, 1):
                (start, stop, step) = (None, None, None)
            try:
                src_dict = table.description._v_colObjects
                # Query the source table and build the result table
                if indices_field_name:
                    # Get the list of indices
                    coordinates = table.getWhereList(condition, condvars, 
                        start=start, stop=stop, step=step)
                    # The array of rows that fullfill the condition
                    selection = table.readCoordinates(coordinates)
                    # Create the destination table: its first column
                    # will contain the indices of the rows selected in
                    # the source table so a new description dictionary
                    # is needed Int64 values are necessary to keep full
                    # 64-bit indices
                    ft_dict = {indices_field_name: tables.Int64Col(pos=-1)}
                    ft_dict.update(src_dict)
                    f_table = self.tmp_h5file.createTable('/', name, ft_dict, 
                                                          title)
                    # Fill the destination table
                    if selection.shape != (0, ):
                        dtype = f_table.read().dtype
                        # A one row array with the proper dtype will be used
                        # to fill the table
                        buffer = \
                        numpy.array([(coordinates[0], ) + tuple(selection[0])], 
                            dtype=dtype)
                        f_table.append(buffer)
                        selection_index = 0
                        for row_index in coordinates[1:]:
                            selection_index = selection_index + 1
                            # Set the first field with the row index
                            buffer[0][0] = row_index
                            # The rest of fields are set using the query result
                            for field_index in range(0, len(dtype) - 1):
                                buffer[0][field_index+1] = \
                                    selection[selection_index][field_index]
                            f_table.append(buffer)
                else:
                    # The array of rows that fullfill the condition
                    selection = table.readWhere(condition, condvars, 
                        start=start, stop=stop, step=step)
                    f_table = self.tmp_h5file.createTable('/', name, src_dict, 
                                                          title)
                    f_table.append(selection)
            except:
                vitables.utils.formatExceptionInfo()
            else:
                f_table.flush()
                # Set some user attributes that define this filtered table
                asi = f_table.attrs
                asi.query_path = query_info['src_filepath']
                asi.query_table = query_info['src_path']
                asi.query_condition = f_table.title
                self.tmp_h5file.flush()

            # Update the list of names in use for filtered tables
            self.ft_names.append(query_info['ft_name'])
            self.last_query = [query_info['src_filepath'], 
                query_info['src_path'], query_info['condition']]
        finally:
            QtGui.qApp.restoreOverrideCursor()

        # RETURN THE RESULT
        return query_info['ft_name']
