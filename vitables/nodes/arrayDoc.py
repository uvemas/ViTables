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
#       $Id: arrayDoc.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the ArrayDoc class.

Classes:

* ArrayDoc(NodeDoc)

Methods:

* __init__(self, dbdoc, nodepath)
* __tr(self, source, comment=None)
* isReadable(self)
* getNodeName(self)
* nodeTitle(self)
* getNodePathName(self)
* getDataType(self)
* getFlavor(self)
* getShape(self)
* numRows(self)
* numCols(self)
* getFilters(self)
* getNodeInfo(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

from vitables.nodes.nodeDoc import NodeDoc
from vitables.vtTables.buffer import Buffer

class ArrayDoc(NodeDoc):
    """
    A data structure that defines a tables.Array or a derived class.

    This class represents a model and is controlled by the leaves
    manager. It exposes methods to get node metadata and data (via
    buffer).
    """


    def __init__(self, dbdoc, nodepath):
        """Creates an array document.

       The document represents an instance of the `tables.Array` class.

        :Parameters:

        - `dbdoc`: the database where node lives
        - `nodepath`: the full path of node in the database object tree
        """

        NodeDoc.__init__(self, dbdoc, nodepath)

        shape = self.getShape()
        # The buffer
        self.buffer = Buffer(self)
        self.getBuffer = self.buffer.readBuffer
        if shape == ():
            # Array element will be read like a[()]
            self.getCell = self.buffer.scalarCell
        elif len(shape) < 2:
            # Array elements will be read like a[row]
            self.getCell = self.buffer.vectorCell
        else:
            # Array elements will be read like a[row][column]
            self.getCell = self.buffer.arrayCell


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('ArrayDoc', source, comment).latin1()


    def isReadable(self):
        """
        Check the dataset readability.

        If the dataset cannot be read then data corruption or missing
        compression libraries are assumed.
        """

        self.getBuffer(0, self.buffer.chunkSize)
        if self.buffer.unreadableDataset:
            filters = self.getFilters()
            print  self.__tr("""\nError: problems reading records. """\
                """The dataset seems to be compressed with """\
                """the %s library. Check that it is installed"""\
                """ in your system, please.""" % filters.complib,
                'A dataset readability error')
        return not self.buffer.unreadableDataset


    def getNodeName(self):
        """:Returns: the node name in the `Python` namespace"""
        return self.node.name


    def nodeTitle(self):
        """
        The array title.

        The `Python` attribute ``title`` is mapped to the system attribute
        ``TITLE``. If it doesn't exist (as it can happen in generic `HDF5`
        arrays) the title attribute is empty.

        :Returns: the ``title`` attribute
        """
        return self.node.title


    def getNodePathName(self):
        """
        :Returns:
            a string representation of the array location in the tree
        """
        return self.node._v_pathname


    def getDataType(self):
        """
        The data type of the represented array.
        VLArrays with atom ObjectAtom and VLStringAtom don't have the
        atom.dtype attribute so we use atom.type in order to get the
        data type.

        :Returns: the data type of the array
        """
        return self.node.atom.type


    def getFlavor(self):
        """
        The flavor attribute of the represented array.

        The `Python` attribute ``flavor`` is mapped to the system attribute
        ``FLAVOR``. If it doesn't exist (as it can happen in generic `HDF5`
        arrays) the flavor attribute is ``numpy``.

        :Returns: the ``flavor`` attribute
        """
        return self.node.flavor


    def getShape(self):
        """:Returns: the shape of the associated data in the array"""
        return self.node.shape


    def numRows(self):
        """
        - `Array.nrows` is the number of rows of the first dimension of the
            array
        - `EArray.nrows`` is the number of rows of the enlargeable dimension
            of the array
        - `VLArray.nrows` is the number of rows of only dimension of the
            array
        - arrays of scalars have no shape and nrows is always 1.

        for `EArray` instances the number of rows of the view may differ
        from the ``nrows`` attribute.

        :Returns: the size of the first dimension of the document
        """

        # The number of rows is obtained from the shape instead of from the
        # nrows attribute
        shape = self.getShape()

        if shape == None:
            # Node is not a Leaf or there was problems getting the shape
            nrows = 0
        elif shape == ():
            # Node is a rank 0 array (e.g. numpy.array(5))
            nrows = 1
        else:
            nrows = shape[0]

        return nrows


    def numCols(self):
        """:Returns: the number of columns"""

        shape = self.getShape()
        if len(shape) > 1:
            # The leaf will be displayed as a bidimensional matrix
            ncolumns = shape[1]
        else:
            # The leaf will be displayed as a column vector
            ncolumns = 1
        return ncolumns


    #
    # These methods are used mainly by the leaves manager in order to display
    # dialogs of properties
    #


    def getFilters(self):
        """:Returns: the ``filters`` attribute of the node"""
        return self.node.filters


    def getNodeInfo(self):
        """
        Get info about the node when it is a Array instance.

        We get the info from `tables.Leaf` instance attributes.
        The following info is returned: type, name, path, dimensions,
        shape, attribute set instance, system attributes and user
        attributes.

        :Returns: a dictionary with information about the array
        """

        info = {}
        # Leaf type
        # Case order matters because both EArray and CArray inherit from
        # Array. VLArray doesn't.
        if self.isInstanceOf('EArray'):
            info['type'] = 'EArray'
        elif self.isInstanceOf('CArray'):
            info['type'] = 'CArray'
        elif self.isInstanceOf('Array'):
            info['type'] = 'Array'
        elif self.isInstanceOf('VLArray'):
            info['type'] = 'VLArray'
        else:
            # Generic HDF5 files
            info['type'] = 'Array'

        # Leaf name
        info['name'] = self.getNodeName()

        # Leaf path
        info['path'] = self.getNodePathName()

        # shape and dimensions
        info['shape'] = self.getShape()
        info['dimensions'] = len(info['shape'])

        # The data type
        info['dataType'] = self.getDataType()

        # filters
        info['filters'] = self.getFilters()

        # Attributes Set Instance and dictionaries
        info['asi'] = self.getASI()
        info['sysAttr'] = self.getNodeAttributes(kind='system')
        info['userAttr'] = self.getNodeAttributes(kind='user')

        return info
