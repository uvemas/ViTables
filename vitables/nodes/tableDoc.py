# -*- coding: utf-8 -*-

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
#       $Id: tableDoc.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the TableDoc class.

Classes:

* TableDoc(NodeDoc)

Methods:

* __init__(self, dbdoc, nodepath)
* __tr(self, source, comment=None)
* isReadable(self)
* getNodeName(self)
* nodeTitle(self)
* getNodePathName(self)
* getShape(self)
* tableColumnsNames(self)
* tableColumnsShapes(self)
* tableColumnsTypes(self)
* numRows(self)
* numCols(self)
* getFilters(self)
* getNodeInfo(self)
* queryTable(self, h5file, query_info, title)
* setDescAttr(self, ftable)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import tables
import numpy

import vitables.utils
from vitables.nodes.nodeDoc import NodeDoc
from vitables.vtTables.buffer import Buffer
from vitables.vtWidgets import queryDlg

class TableDoc(NodeDoc):
    """
    A data structure that defines a tables.Table.

    This class represents a model and is controlled by the leaves
    manager. It exposes methods to get node metadata and data (via
    buffer).
    """


    def __init__(self, dbdoc, nodepath):
        """
        Creates a document that represents a tables.Table.

        Message like ``Warning: Encountered invalid numeric result(s) in...``
        appears from time to time when floating point columns of tables are
        queried. However the query result are correct. We get rid of those
        messages using the numpy support for error handling.
        
        :Parameters:

        - `dbdoc`: the database where node lives
        - `nodepath`: the full path of node in the database object tree
        """

        NodeDoc.__init__(self, dbdoc, nodepath)

        # The buffer
        self.buffer = Buffer(self)
        self.getBuffer = self.buffer.readBuffer
        self.getCell = self.buffer.arrayCell

        numpy.seterr(invalid='ignore')


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('TableDoc', source, comment).latin1()


    def isReadable(self):
        """
        Check the dataset readability.

        If the dataset cannot be read then data corruption or missing
        compression libraries are assumed.
        """

        self.getBuffer(0, self.buffer.chunkSize)
        if self.buffer.unreadableDataset:
            filters = self.getFilters()
            print  self.__tr("""\nError: problems reading records."""\
                """The dataset seems to be compressed with """\
                """the %s library. Check that it is installed"""\
                """ in your system, please.""" % filters.complib,
                'A dataset readability error')
        return not self.buffer.unreadableDataset


    def getNodeName(self):
        """:Returns: the node name in `Python` namespace"""
        return self.node.name


    def nodeTitle(self):
        """
        The node title.

        The Python attribute ``title`` is mapped to the system attribute
        ``TITLE``. If it doesn't exist (as it can happen in generic `HDF5`
        arrays) the title attribute is empty.

        :Returns: the ``title`` attribute
        """
        return self.node.title


    def getNodePathName(self):
        """
        :Returns: a string representation of the node location in the tree
        """
        return self.node._v_pathname


    def getShape(self):
        """:Returns: the shape of the associated data in a leaf"""
        return self.node.shape


    def tableColumnsNames(self):
        """:Returns: a list with the field names for `Table` instances"""
        return self.node.colnames


    def tableColumnsShapes(self):
        """:Returns: a dictionary with the shapes for the `Table` fields"""

        coldescrs = self.node.coldescrs
        return dict((k, v.shape) for (k, v) in coldescrs.iteritems())


    def tableColumnsTypes(self):
        """:Returns: a dictionary with the types for the table fields"""
        return self.node.coltypes


    def numRows(self):
        """:Returns: the size of the first dimension of the document"""
        return self.node.nrows


    def numCols(self):
        """:Returns: the number of columns"""
        return len(self.tableColumnsNames())


    def getFilters(self):
        """:Returns: the filters attribute of the node
        """
        return self.node.filters


    #
    # These methods are used mainly by the leaves manager in order to display
    # dialogs of properties
    #


    def getNodeInfo(self):
        """
        Get info about the node when it is a `Table` instance.

        We read the following `Table` attributes: ``name``,
        ``_v_pathname``, ``shape``, ``attrs``, ``colnames``,
        ``coltypes`` and ``colshapes``). They are used to build a map
        with the following info: type, name, path, dimensions,
        shape, data type, members, attribute set instance, system
        attributes and user attributes.

        :Returns: a dictionary with information about the table
        """

        info = {}
        # Leaf type
        info['type'] = 'Table'

        # Leaf name
        info['name'] = self.getNodeName()

        # Leaf path
        info['path'] = self.getNodePathName()

        # shape
        info['shape'] = self.getShape()
        info['dimensions'] = len(info['shape'])

        # filters
        info['filters'] = self.getFilters()

        # Leaf data type
        info['dataType'] = 'Record'

        # Attributes Set Instance and dictionaries
        info['asi'] = self.getASI()
        info['sysAttr'] = self.getNodeAttributes(kind='system')
        info['userAttr'] = self.getNodeAttributes(kind='user')

        # coltypes and colshapes are Table instance variables
        coltypes = self.tableColumnsTypes()
        colshapes = self.tableColumnsShapes()
        # Nested fields appear as (colname, nested, -) in the Properties dlg
        info['members'] = []
        # Look for nested fields
        for pathname in self.node.colpathnames:
            if pathname.count('/'):
                pathname = pathname.split('/')[0]
                ctype = 'nested'
                cshape = '-'
            else:
                ctype = coltypes[pathname]
                cshape = colshapes[pathname]
            if not (pathname, ctype, cshape) in info['members']:
                info['members'].append((pathname, ctype, cshape))

        return info


    def queryTable(self, h5file, query_info, title):
        """
        Add a new filtered table to the temporary database.

        :Parameters:
     
        - `h5file`:
            the file (`tables.File` instance) where the table will be added
        - `query_info`: a dictionary with information about the query
        - `title`: the title of the result table
        """
    
        src_table = self.node
        # Define shorthands
        (start, stop, step) = query_info['rows_range']
        name = query_info['ft_name']
        condition = query_info['condition']
        condvars = query_info['condvars']
        indices_field_name = query_info['indices_field_name']
    
        # If no slice is passed the best choice is to set the start, stop, step
        # arguments to None. It is due to the implementation of readWhere
        if (start,  stop, step) == (0, src_table.nrows, 1):
            (start, stop, step) = (None, None, None)
        try:
            src_dict = src_table.description._v_colObjects
            # Query the source table and build the result table
            if indices_field_name:
                # Get the list of indices
                coordinates = src_table.getWhereList(condition, condvars, 
                    start=start, stop=stop, step=step)
                # The array of rows that fullfill the condition
                selection = src_table.readCoordinates(coordinates)
                # Create the destination table: its first column will contain
                # the indices of the rows selected in the source table
                # so a new description dictionary is needed
                # Int64 values are necessary to keep full 64-bit indices
                ft_dict = {indices_field_name: tables.Int64Col(pos=-1)}
                ft_dict.update(src_dict)
                f_table = h5file.createTable('/', name, ft_dict, title)
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
                selection = src_table.readWhere(condition, condvars, 
                    start=start, stop=stop, step=step)
                f_table = h5file.createTable('/', name, src_dict, title)
                f_table.append(selection)
        except:
            vitables.utils.formatExceptionInfo()
        else:
            f_table.flush()
            # Set some user attributes that define this filtered table
            self.setDescAttr(f_table)
            h5file.flush()
            return f_table.nrows


    def setDescAttr(self, ftable):
        """
        A set of user attributes that describe a query.

        Three attributes are set:

        :query_path: contains the full path of the queried file
        :query_table: contains the full nodepath of the queried table
        :query_condition: contains the string representation of the query
    
        :Parameter ftable: a table with the result of a table query
        """
    
        asi = ftable.attrs
        asi.query_path = self.filepath
        asi.query_table = self.nodepath
        asi.query_condition = ftable.title


