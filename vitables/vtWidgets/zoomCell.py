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
#       $Id: zoomCell.py 1083 2008-11-04 16:41:02Z vmas $
#
########################################################################

"""Here is defined the ZoomCell class.

Classes:

* ZoomCell(qttable.QTable)

Methods:

* __init__(self, cell, caption, workspace, name=None)
* hasShape(self)
* getGridDimensions(self)
* getPyObjectDimensions(self)
* getArrayDimensions(self, shape)
* getTableDimensions(self, dtype)
* zoomTable(self)
* zoomArray(self)
* slotZoomView(self, row, col, button, position)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import numpy

import tables.utilsExtension

import qt
import qttable

import vitables.utils
from vitables.vtWidgets.vtTableItem import VTTableItem

class ZoomCell(qttable.QTable):
    """
    Display an array/table cell on its own view (table widget).

    When a leaf is displayed in a view, is quite usual that the content
    of some cells is not fully visible because it doesn't fit into
    the cell. To alleviate this problem this class provides a way to,
    recursively, display the content of any cell on its own view.
    The cell content depends on the kind of leaf and the shape of its
    atom. Cells of `Table` views and `E/C/Array` views can be:

    - a `numpy` scalar. `Atom` shape is ()
    - a `numpy` array. `Atom` shape is not ()

    In addition, cells of `VLArray` views can be:

    - a serialized `Python` object. `Atom` kind is ``object``, shape is ()
    - a `Python` string. `Atom` kind is ``vlstring``, shape is ()

    Finally, cells of `Table` views also can be:

    - a `numpy.void` object when the cell corresponds to nested field of the record
    """


    def __init__(self, cell, caption, workspace, name=None):
        """
        Creates a zoom view for a given cell.

        The passed cell is an element of a given dataset. It is always
        a (potentially nested) `numpy` array. See cell accessor methods
        in the `Buffer` class for details.

        :Parameters:

            - `cell`: the value stored in the cell
            - `caption`: the base string for the zoomed view caption
            - `workspace`: the parent of the view
        """

        self.workspace = workspace
        self.zvCaption = caption
        self.cellData = cell
        self.cellHasShape = self.hasShape()
        self.fieldNames = []
        # Decide how the cell content will be formatted. Content can be:
        # - a numpy array
        # - either a string or a unicode string
        # - other Python object
        if self.cellHasShape:
            self.formatContent = vitables.utils.formatArrayContent
        elif isinstance(cell, str) or isinstance(cell, unicode):
            self.formatContent = vitables.utils.formatStringContent
        else:
            self.formatContent = vitables.utils.formatObjectContent

        # Create and customise the widget that will display the zoomed cell
        # The WDestructiveClose flag makes that when the widget is
        # closed either programatically (see VTAPP.slotWindowsClose)
        # or by the user (clicking the close button in the titlebar)
        # the widget is hiden AND destroyed --> the workspace
        # updates automatically its list of open windows --> the
        # Windows menu content is automatically updated
        (nrows, ncols) = self.getGridDimensions()
        qttable.QTable.__init__(self, nrows, ncols, workspace, name)
        self.setWFlags(qt.QWidget.WDestructiveClose)
        self.setReadOnly(1)

        # Use customised QTableItems to properly align the contents.
        header = self.verticalHeader()
        font_metrics = qt.QFontMetrics(self.fontMetrics())
        font_height = font_metrics.height()
        for row in range(0, nrows):
            header.resizeSection(row, font_height*1.2)
            for col in range(0, ncols):
                self.setItem(row, col, VTTableItem(self, ro=False))

        # Configure the titlebar
        self.setCaption(self.zvCaption)
        iconsDictionary = vitables.utils.getIcons()
        self.setIcon(iconsDictionary['zoom'].pixmap(qt.QIconSet.Small,
            qt.QIconSet.Normal, qt.QIconSet.On))

        # Setup the horizontal header for zooms of Table fields
        if self.fieldNames:
            header = self.horizontalHeader()
            for section in range(0, ncols):
                header.setLabel(section, self.fieldNames[section])

        # Fill the zoom view
        if self.fieldNames:
            self.zoomTable()
        else:
            self.zoomArray()

        # Without this (empirical) resizing all windows would be placed at
        # the workspace origin
        self.resize(300,300)

        # Once the geometry arrangements (implicits via fillTable or 
        # explicits via resize) are done we show the view.
        self.show()

        # Resize the view as nicely as I can
        while self.visibleHeight() > self.contentsHeight():
            delta = self.visibleHeight() - self.contentsHeight()
            self.resize(self.width(), self.height() - delta)
        while self.visibleWidth() > self.contentsWidth():
            delta = self.visibleWidth() - self.contentsWidth()
            self.resize(self.width() - delta, self.height())

        if self.numCols() == 1:
            self.setColumnStretchable(0, 1)
        if self.numRows() == 1:
            self.setRowStretchable(0, 1)

        # Connect signals to slots
        self.connect(self,
            qt.SIGNAL('doubleClicked(int, int, int, const QPoint &)'),
            self.slotZoomView)


    def hasShape(self):
        """Find out if the cell has a shape attribute."""

        if hasattr(self.cellData, 'shape'):
            return True
        else:
            return False


    def getGridDimensions(self):
        """
        Get the dimensions of the grid where the cell will be zoomed.

        Any zoomed cell will be displayed in a table with dimensions
        `(nrows, ncols)`

        :Returns: a tuple (rows, columns)
        """

        if self.cellHasShape:
            # The cell contains a numpy object
            shape = self.cellData.shape
            dtype = self.cellData.dtype
            if dtype.fields:
                # Table nested fields come here
                return self.getTableDimensions(dtype)
            else:
                # Any other case come here
                return self.getArrayDimensions(shape)
        else:
            # The cell contains a Python object
            return self.getPyObjectDimensions()


    def getPyObjectDimensions(self):
        """
        Get the dimensions of the grid where the cell will be zoomed.

        The zoomed cell contains a `Python` object.

        :Returns: a tuple (rows, columns)
        """

        if isinstance(self.cellData, list) or isinstance(self.cellData, tuple):
            return (len(self.cellData), 1)
        else:
            return (1, 1)


    def getArrayDimensions(self, shape):
        """
        Get the dimensions of the grid where the cell will be zoomed.

        The zoomed cell contains a `numpy` array and will be displayed
        in a table with the same shape than it.

        :Parameter shape: the cell shape

        :Returns: a tuple (rows, columns)
        """

        # Numpy scalars are special a case
        if shape == ():
            nrows = ncols = 1
        # 1-D arrays are displayed as a 1-column vector with nrows
        elif len(shape) == 1:
            nrows = shape[0]
            ncols = 1
        # N-D arrays are displayed as a matrix (nrowsXncols) which
        # elements are (N-2)-D arrays
        else:
            nrows = shape[0]
            ncols = shape[1]

        return (nrows, ncols)


    def getTableDimensions(self, dtype):
        """
        Get the dimensions of the grid where the cell will be zoomed.

        The zoomed cell contains a nested field and will be displayed
        in a table with only one row and one column per (top - 1)
        level field. Note that fields have `shape`=().

        :Parameter dtype: the cell data type

        :Returns: a tuple (rows, columns)
        """

        self.fieldNames = [name for (name, format) in self.cellData.dtype.descr]
        ncols = len(self.fieldNames)
        nrows = 1

        return (nrows, ncols)


    def zoomTable(self):
        """Fill the zoom view with the content of the clicked nested field."""

        for column in range(0, self.numCols()):
            content = self.cellData[self.fieldNames[column]]
            text = self.formatContent(content)
            self.setText(0, column, text)


    def zoomArray(self):
        """Fill the zoom view with the content of the clicked cell."""

        numRows = self.numRows()
        numCols = self.numCols()
        # Numpy scalars are displayed in a 1x1 grid
        if numRows == numCols == 1:
            content = self.cellData
            text = self.formatContent(content)
            self.setText(0, 0, text)
        # 1-D arrays
        elif numCols == 1:
            for row in range(0, numRows):
                content = self.cellData[row]
                text = self.formatContent(content)
                self.setText(row, 0, text)
        # N-D arrays
        else:
            for row in range(0, numRows):
                for column in range(0, numCols):
                    content = self.cellData[row][column]
                    text = self.formatContent(content)
                    self.setText(row, column, text)


    def slotZoomView(self, row, col, button, position):
        """Makes the content of the clicked cell fully visible.

        :Parameters:

            - `row`: the row of the clicked cell
            - `col`: the column of the clicked cell
            - `button`: the mouse button pressed
            - `position`: the mouse position. Not used.
        """

        # Check if the zoom has to be done
        if button != qt.Qt.LeftButton:
            return
        elif self.cellHasShape:
            if not (self.cellData.shape !=() or self.fieldNames):
                return
        elif not (isinstance(self.cellData, list) or isinstance(self.cellData, tuple)):
                return

        # Get data
        if self.cellHasShape:
            # Arrays and table nested fields
            if self.fieldNames:
                cell = self.cellData[self.fieldNames[col]]
            elif len(self.cellData.shape) > 1:
                cell = self.cellData[row][ col]
            elif len(self.cellData.shape) == 1:
                cell = self.cellData[row]
        else:
            # Python lists and tuples
            cell = self.cellData[row]

        # Get caption
        if self.fieldNames:
            caption = '%s: %s[%s]' % (self.zvCaption,
                self.fieldNames[col], row + 1)
        else:
            caption = '%s: (%s, %s)' % (self.zvCaption, row + 1, col + 1)
        ZoomCell(cell, caption, self.workspace)
