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
#       $Id: systemAttr.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the SysAttrPage class.

Classes:

* SysAttrPage(qt.QWidget)

Methods:

* __init__(self, info, mode='r')
* __tr(self, source, comment=None)
* getTitleAttr(self)
* getAttrTable(self)
* makeAttrPage(self, attr_map, mode)
* makeAttrTable(self, attr_map, mode)
* slotDisplayCellContent(self, row, col, button, mouse_position)
* slotEditCell(self, row, col)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import tables

import qt
import qttable

import vitables.utils
from vitables.vtWidgets.vtTableItem import VTTableItem

class SysAttrPage(qt.QWidget):
    """The System Attributes page of Properties dialogs."""


    def __init__(self, info, mode='r'):
        """:Parameters:

        - `info`: the system attributes dictionary
        - `mode`: the access mode of the database to which the selected node
            belongs. Can be 'r'ead-only, 'w'rite or 'a'ppend.
        """

        qt.QWidget.__init__(self)
        self.page_layout = qt.QVBoxLayout(self, 10, 6)

        # Makes the attributes page
        self.attr_table = qttable.QTable(self)
        self.cc_display = vitables.utils.makeLineEdit('', self, False, True)
        self.makeAttrPage(info, mode)

        self.connect(self.attr_table,
            qt.SIGNAL('clicked(int, int, int,const QPoint&)'),
            self.slotDisplayCellContent)

        if mode != 'r':
            self.connect(self.attr_table,
                qt.SIGNAL('clicked(int, int, int,const QPoint&)'),
                self.slotEditCell)


    def __tr(self, source, comment=None):
        """Translate method.""" 
        return qt.qApp.translate('SysAttrPage', source, comment).latin1()


    def getTitleAttr(self):
        """
        Return the ``TITLE`` system attribute.

        Inspect the table of system attributes and get the string value
        of the ``TITLE`` attribute.
        """

        for row in range(0, self.attr_table.numRows()):
            if self.attr_table.text(row, 0).latin1() == 'TITLE':
                title = self.attr_table.text(row, 1).latin1()
                # QString('').latin1() is '' but QString().latin1() is None
                if title is None:
                    title = ''
                return title


    def getAttrTable(self):
        """:Returns: the attributes table."""
        return self.attr_table


    def makeAttrPage(self, attr_map, mode):
        """
        Makes the User/System Attributes page.

        Layout schema
        -------------
        ::

            root --> grid layout
                labelName + labelValue
                table

        :Parameters:

        - `attr_map`: the attributes dictionary
        - `mode`: the access mode to the system attributes
        """

        # FIRST ROW System attributes: value
        attr_label = qt.QLabel(self.__tr('System attributes:',
            'Label of the system attributes input box'), self)
        vitables.utils.addRow(attr_label, str(len(attr_map)), self)

        # SECOND ROW --> the attributes table
        self.page_layout.addWidget(self.attr_table)
        self.makeAttrTable(attr_map, mode)

        # THIRD ROW --> the cell contents displayer
        self.page_layout.addWidget(self.cc_display)


    def makeAttrTable(self, attr_map, mode):
        """
        Makes and configures the attributes table.

        Attributes table has 3 columns: ``Name``, ``Value`` and ``DataType``.

        :Parameters:

        - `attr_map`: a dictionary with the node system attributes
        - `mode`: the access mode to the system attributes
        """

        self.attr_table.setNumRows(len(attr_map))
        self.attr_table.setNumCols(3)

        # System attributes (name, value) list
        attr_items = attr_map.items()
        attr_items.sort()

        # Fills up the attributes table with the proper values
        # Use customised QTableItems that align cell content allways to left
        row = 0
        for (name, value) in attr_items:
            # First find out the attribute datatype
            if isinstance(value, tables.Filters):
                dtype_name = 'tables.filters.Filters'
            elif isinstance(value, str):
                dtype_name = 'string'
            # Since PyTables 1.1 scalar attributes are stored as numarray arrays
            # Since PyTables 2.0 scalar attributes are stored as numpy arrays
            elif hasattr(value, 'shape'):
                dtype_name = value.dtype.name
            else:
                # The attributes are scalar Python objects (PyTables<1.1)
                # or N-dimensional attributes
                dtype_name = str(type(value))

            # Setup the name cell
            self.attr_table.setItem(row, 0, VTTableItem(self.attr_table,
                ro=True))
            self.attr_table.setText(row, 0, name)

            # Setup the value cell
            if (name == 'TITLE') and (mode != 'r'):
                # This attribute is only set if the dataset is opened in
                # read-write mode.
                self.attr_table.setItem(row, 1, VTTableItem(self.attr_table,
                ro =False))
            else:
                self.attr_table.setItem(row, 1, VTTableItem(self.attr_table,
                    ro=True))
            self.attr_table.setText(row, 1, str(value))

            # Setup the datatype cell
            self.attr_table.setItem(row, 2, VTTableItem(self.attr_table,
                ro=True))
            self.attr_table.setText(row, 2, dtype_name)
            row = row + 1

        # Configure sizes
        self.attr_table.resize(self.attr_table.sizeHint())
        self.attr_table.setColumnStretchable(0, True)
        self.attr_table.setColumnStretchable(1, True)
        self.attr_table.setColumnStretchable(2, True)

        # Set labels for horizontal sections
        hor_header = self.attr_table.horizontalHeader()
        hor_header.setLabel(0, self.__tr('Name',
            'First column header of the attributes table'))
        hor_header.setLabel(1, self.__tr('Value',
            'Second column header of the attributes table'))
        hor_header.setLabel(2, self.__tr('DataType',
            'Third column header of the attributes table'))

        # Hide vertical header
        self.attr_table.verticalHeader().hide()
        self.attr_table.setLeftMargin(0)

        # Give table a non editable look
        # By default tables' background is white and they look like an
        # editable widget
        self.attr_table.setPaletteBackgroundColor(self.attr_table.eraseColor())

        # Unbold the font
        font = self.font()
        font.setBold(0)
        self.attr_table.viewport().setFont(font)


    def slotDisplayCellContent(self, row, col, button, mouse_position):
        """Show the content of the clicked cell in the line edit at bottom."""

        if button == qt.Qt.LeftButton:
            content = self.attr_table.text(row, col)
            self.cc_display.clear()
            self.cc_display.setText(content)


    def slotEditCell(self, row, col):
        """
        Edit the TITLE attribute.

        If the node is opened in read-write mode its TITLE attribute is edited.

        :Parameters:

        - `row`: the clicked row
        - `col`: the clicked column
        """

        # In table of system attributes the cell containing the TITLE
        # value will have EditType QTableItem.OnTyping if the node is
        # in read-write mode
        if self.attr_table.item(row, col).editType() == qttable.QTableItem.OnTyping:
            self.attr_table.editCell(row, col)
            self.attr_table.update()
