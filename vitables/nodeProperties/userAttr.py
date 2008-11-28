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
#       $Id: userAttr.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the UserAttrPage class.

Classes:

* UserAttrPage(qt.QWidget)

Methods:

* __init__(self, info, mode='r')
* __tr(self, source, comment=None)
* getAttrTable(self)
* makeAttrPage(self, attr_map, mode)
* makeAttrTable(self, attr_map, mode)
* makeButton(self, label, mode)
* slotEnterHelpMode(self)
* slotDisplayCellContent(self, row, col, button, mouse_position)
* slotEditCell(self, row, col)
* slotAddAttr(self)
* slotDelAttr(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt
import qttable

import vitables.utils
from vitables.vtWidgets.vtTableItem import VTTableItem

class UserAttrPage(qt.QWidget):
    """The User Attributes page of Properties dialogs."""


    def __init__(self, info, mode='r'):
        """:Parameters:

        - `info`: the user attributes dictionary
        - `mode`: the access mode of the database to which the selected node
            belongs. Can be 'r'ead-only, 'w'rite or 'a'ppend.
        """

        qt.QWidget.__init__(self)
        self.page_layout = qt.QVBoxLayout(self, 10, 6)

        self.user_attr_edited = False

        datatypes = """int8 int16 int32 int64 uint8 uint16 uint32 uint64 """\
        """float32 float64 complex64 complex128 bool string python"""
        self.dtypes_list = qt.QStringList.split(' ', datatypes)

        # Some page widgets
        self.attr_table = qttable.QTable(self)
        qt.QWhatsThis.add(self.attr_table, self.__tr(
            """<qt>
            <h3>User's attributes editing table</h3>
            Here you can perform the editing of user's attributes for
            this node. It is quite straightforward. <p>For adding an
            attribute click the <b>Add</b> button. A new row will
            be added to the table. Enter the attribute name and its
            value in the corresponding cells. Finally, select the
            attribute datatype in the combobox of the DataType column.
            In order to delete an attribute just select it by clicking
            any of its cells, then click the <b>Delete</b> button.</p>
            <p>Beware that PyTables stores scalar attributes as numpy
            scalar arrays so you will be unable to save them as Python
            objects even if you choose the Python datatype in the
            combobox selector. Also note that multidimensional attributes
             other than Python lists and tuples are not supported.</p>
            </qt>""",
            'Help text for the User Attributes page')
            )
        self.cc_display = vitables.utils.makeLineEdit('', self, False, True)
        self.add_button = self.makeButton(self.__tr('&Add',
            'Label of the Add button'), mode)
        self.del_button = self.makeButton(self.__tr('&Delete',
            'Label of the Delete button'), mode)
        self.help_button = self.makeButton(self.__tr("&What's This",
            'Label of the Help button'), 'a')
        # Makes the attributes page
        self.makeAttrPage(info, mode)

        self.connect(self.add_button, qt.SIGNAL('clicked()'), self.slotAddAttr)
        self.connect(self.del_button, qt.SIGNAL('clicked()'), self.slotDelAttr)
        self.connect(self.help_button, qt.SIGNAL('clicked()'),
            self.slotEnterHelpMode)

        self.connect(self.attr_table,
            qt.SIGNAL('clicked(int, int, int,const QPoint&)'),
            self.slotDisplayCellContent)

        if mode != 'r':
            self.connect(self.attr_table,
                qt.SIGNAL('currentChanged(int, int)'),
                self.slotEditCell)
            self.connect(self.attr_table,
                qt.SIGNAL('clicked(int, int, int,const QPoint&)'),
                self.slotEditCell)

    def __tr(self, source, comment=None):
        """Translate method.""" 
        return qt.qApp.translate('UserAttrPage', source, comment).latin1()


    def getAttrTable(self):
        """Return the attributes table."""
        return self.attr_table


    def makeAttrPage(self, attr_map, mode):
        """
        Makes the User Attributes page.

        Layout schema
        -------------
        ::

            labelName + labelValue
            table
            buttons

        :Parameters:

        - `attr_map`: the attributes dictionary
        - `mode`: the access mode to the user attributes
        """


        # FIRST ROW User attributes: value
        attr_label = qt.QLabel(self.__tr('User attributes:',
            'Label of the user attributes input box'), self)
        vitables.utils.addRow(attr_label, str(len(attr_map)), self)

        # SECOND ROW --> the attributes table
        self.page_layout.addWidget(self.attr_table)
        self.makeAttrTable(attr_map, mode)

        # THIRD ROW --> the cell contents displayer
        self.page_layout.addWidget(self.cc_display)

        # FOURTH ROW --> edition buttons
        # The Add button
        buttons_layout = qt.QHBoxLayout(self.page_layout, 6)
        # The Delete button
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.del_button)
        buttons_layout.addWidget(self.help_button)
        buttons_layout.addStretch(1)


    def makeAttrTable(self, attr_map, mode):
        """
        Makes and configures the attributes table.

        Attributes table has 3 columns: ``Name``, ``Value`` and ``DataType``.

        :Parameters:

        - `attr_map`: a dictionary with the node user attributes
        - `mode`: the access mode to the user attributes
        """

        self.attr_table.setNumRows(len(attr_map))
        self.attr_table.setNumCols(3)

        # We will not be able to delete several attributes at once
        self.attr_table.setSelectionMode(qttable.QTable.NoSelection)

        # System attributes (name, value) list
        attr_items = attr_map.items()
        attr_items.sort()

        # Fills up the attributes table with the proper values
        # Use customised QTableItems that align cell content allways to left
        row = 0
        for (name, value) in attr_items:
            # In PyTables < 1.1 scalar attributes are stored as Python objects
            # In PyTables >=1.1 scalar attributes are stored as numarray arrays
            # In PyTables >= 2.0 scalar attributes are stored as numpy arrays
            if hasattr(value, 'shape'):
                dtype_name = value.dtype.name
                if dtype_name.startswith('string'):
                    dtype_name = 'string'
            else:
                # But attributes can also be non scalar Python objects.
                dtype_name = 'Python'
            dtype_cw = qttable.QComboTableItem(self.attr_table,
                self.dtypes_list)
            dtype_cw.setCurrentItem(dtype_name)
            dtype_cw.setEditable(0)

            value = str(value)
            if dtype_name.startswith('complex'):
                # Remove parenthesis from the str representation of
                # complex numbers.
                value = value[1:-1]

            # ViTables doesn't support editing ND-array attributes so
            # they are displayed in not editable cells
            if (hasattr(value, 'shape') and value.shape != ())or\
            (mode == 'r'):
                read_only = True
            else:
                read_only = False

            self.attr_table.setItem(row, 0, VTTableItem(self.attr_table,
                read_only, name))
            self.attr_table.setItem(row, 1, VTTableItem(self.attr_table,
                read_only, value))
            self.attr_table.setItem(row, 2, dtype_cw)
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

        # Give table a non editable look (if needed)
        if mode == 'r':
            self.attr_table.setPaletteBackgroundColor(self.attr_table.eraseColor())
        
        # Unbold the font
        font = self.font()
        font.setBold(0)
        self.attr_table.viewport().setFont(font)


    def makeButton(self, label, mode):
        """
        Create and setup a button.

        :Parameters:

        - `label`: the button translated label
        - `mode`: indicates if the button is enabled or not

        :Returns: the created button
        """

        button = qt.QPushButton(label, self)
        # Sets the button font
        font = self.font()
        font.setBold(False)
        button.setFont(font)
        # Sets the activation state
        if mode == 'r':
            button.setEnabled(0)
        else:
            button.setEnabled(1)
        return button


    # SLOT methods for user attributes


    def slotEnterHelpMode(self):
        """Makes the dialog to enter in help mode."""
        qt.QWhatsThis.enterWhatsThisMode()


    def slotDisplayCellContent(self, row, col, button, mouse_position):
        """Show the content of the clicked cell in the line edit at bottom."""

        if button == qt.Qt.LeftButton:
            content = self.attr_table.text(row, col)
            self.cc_display.clear()
            self.cc_display.setText(content)


    def slotEditCell(self, row, col):
        """When a cell becomes current it is edited."""

        self.user_attr_edited = True
        if col < 2:
            self.attr_table.editCell(row, col)
            self.attr_table.update()


    def slotAddAttr(self):
        """Adds a new user attribute to the attributes table.

        This slot is connected to the clicked signal of the ``Add`` button.
        """

        self.user_attr_edited = True

        last_row = self.attr_table.numRows()
        self.attr_table.insertRows(last_row, 1)
        dtypes_cw = qttable.QComboTableItem(self.attr_table, self.dtypes_list)
        dtypes_cw.setEditable(0)
        self.attr_table.setItem(last_row, 0, VTTableItem(self.attr_table,
            ro=False))
        self.attr_table.setItem(last_row, 1, VTTableItem(self.attr_table,
            ro=False))
        self.attr_table.setItem(last_row, 2, dtypes_cw)
        self.attr_table.update()

        # Usability enhancements

        # Gives focus to the proper cell. If not, clicking Add+Delete
        # results in a different attribute deletion
        self.attr_table.setCurrentCell(last_row, 0)
        # Editing starts automatically in the Name cell
        self.slotEditCell(last_row, 0)


    def slotDelAttr(self):
        """
        Deletes a user attribute.

        This slot is connected to the clicked signal of the Delete button.
        An attribute is marked for deletion by giving focus to any cell
        of the row describing it (i.e. clicking a cell or selecting its
        contents.
        """

        self.user_attr_edited = True

        current_row = self.attr_table.currentRow()
        # Look for an attribute marked for deletion
        marked = False
        for col in range(0, self.attr_table.numCols()):
            if self.attr_table.item(current_row, col).isEnabled():
                marked = True

        # If there are not marked attributes then print an info message
        if not marked:
            print self.__tr('Please, select the attribute to be deleted.',
                'A usage text')
            return

        # Delete the marked attribute
        name_cell = self.attr_table.text(current_row, 0)
        del_mb = qt.QMessageBox.question(self.parent(),
            self.__tr('User attribute deletion',
            'Caption of the attr deletion dialog'),
            self.__tr("""\n\nYou are about to delete the attribute:\n%s\n\n""",
            'Ask for confirmation') % name_cell.latin1(),
            qt.QMessageBox.Ok|qt.QMessageBox.Default,
            qt.QMessageBox.Cancel|qt.QMessageBox.Escape,
            qt.QMessageBox.NoButton)

        # OK returns Accept, Cancel returns Reject
        if del_mb == qt.QMessageBox.Ok:
            # Updates the user attributes table
            self.attr_table.removeRow(current_row)
            self.attr_table.update()

