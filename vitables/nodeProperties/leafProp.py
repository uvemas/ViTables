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
#       $Id: leafProp.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the LeafGeneralPage class.

Classes:

* LeafGeneralPage(qt.QWidget)

Methods:

* __init__(self, info)
* __tr(self, source, comment=None)
* arrayGeneralPage(self)
* tableGeneralPage(self)
* makeTable(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt
import qttable

import vitables.utils
from vitables.vtWidgets.vtTableItem import VTTableItem

class LeafGeneralPage(qt.QWidget):
    """
    Makes the ``General`` page of leaves properties dialog.

    Layout schema for arrays::

        root --> vbox layout
            database group box --> grid layout
                3*[labelName, labelValue, spacer]
            dataspace group box --> grid layout
                3*[labelName, labelValue, spacer]

    Layout schema for tables::

        root --> vbox layout
            database group box --> vertical layout
                3*[labelName, labelValue]
            dataspace group box --> vertical layout
                3*[labelName, labelValue]
                table
    """
    
    def __init__(self, info):
        """:Parameter info: a dictionary with the information to be displayed"""

        qt.QWidget.__init__(self)
        self.page_layout = qt.QVBoxLayout(self, 10, 6)
        self.gb_dataspace = qt.QGroupBox(
            self.__tr('Dataspace', 'Title of the groupbox'), self)

        self.info = info
        if self.info['type'] == 'Table':
            self.records = qttable.QTable(self.gb_dataspace)
            self.tableGeneralPage()
        else:
            self.arrayGeneralPage()


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('LeafGeneralPage', source, comment).latin1()


    def arrayGeneralPage(self):
        """Makes the ``General`` page for `Array` nodes."""

        #
        # Database is a GroupBox with grid layout #############################
        #

        gb_database = qt.QGroupBox(self.__tr('Database', 'Groupbox title'),
            self)
        gb_database.setOrientation(qt.Qt.Vertical)
        gb_database.setInsideMargin(10)
##        gb_database.setInsideSpacing(6) # Doesn't work, PyQt bug??
        gb_database.layout().setSpacing(6)
        
        # Other apparently equivalent code doesn't work:
##        databaseL = qt.QVBoxLayout(gb_database, 10, 6)
        # Or even:
##        gb_database = qt.QGroupBox(3, qt.Qt.Vertical, self.__tr('Database',
##            'Title of the groupbox'), self)
##        gb_database.setInsideMargin(10)
##        gb_database.setInsideSpacing(6)

        # FIRST ROW Name: value
        name_label = qt.QLabel(
            self.__tr('Name:', 'Label of the leaf name text box'),
            gb_database)
        vitables.utils.addRow(name_label, self.info['name'], gb_database)

        # SECOND ROW Path: value
        path_label = qt.QLabel(
            self.__tr('Path:', 'Label of the leaf full path text box'),
            gb_database)
        vitables.utils.addRow(path_label, self.info['path'], gb_database)

        # THIRD ROW Type: value
        type_label = qt.QLabel(
            self.__tr('Type:', 'Label of the dataset type text box'),
            gb_database)
        vitables.utils.addRow(type_label, self.info['type'], gb_database)

        # Adds the GroupBox to the General page layout
        self.page_layout.addWidget(gb_database)

        #
        # Dataspace is a GroupBox with a grid layout #################
        #

        self.gb_dataspace.setOrientation(qt.Qt.Vertical)
        self.gb_dataspace.setInsideMargin(10)
##        self.gb_dataspace.setInsideSpacing(6) # Doesn't work, PyQt bug??
        self.gb_dataspace.layout().setSpacing(6)

        # FIRST ROW Dimensions: value
        dimensions_label = qt.QLabel(self.__tr('Dimensions:',
            'Label of the number of dimensions text box'), self.gb_dataspace)
        vitables.utils.addRow(dimensions_label, str(self.info['dimensions']),
            self.gb_dataspace)

        # SECOND ROW Shape: value
        shape_label = qt.QLabel(
            self.__tr('Shape:', 'Label of the shape text box'),
            self.gb_dataspace)
        shape = str(self.info['shape'])
        vitables.utils.addRow(shape_label, shape, self.gb_dataspace)

        # THIRD ROW Data Type: value
        dtype_label = qt.QLabel(
            self.__tr('Data Type:', 'Label of the data type text box'),
            self.gb_dataspace)
        vitables.utils.addRow(dtype_label, str(self.info['dataType']),
            self.gb_dataspace)

        # FOURTH ROW Filters: value
        filters_label = qt.QLabel(
            self.__tr('Compression:', 'Label of the Filter text box'),
            self.gb_dataspace)
        # Since PyTables 2.x filters.complib can be None so we force a str
        vitables.utils.addRow(filters_label, self.info['filters'].complib or \
            'None', self.gb_dataspace)

        # Adds the GroupBox to the General page layout
        self.page_layout.addWidget(self.gb_dataspace)


    def tableGeneralPage(self):
        """Makes the ``General`` page for `Table` nodes."""

        self.arrayGeneralPage()

        # Adds a new row to the dataspace grid layout
        # LAST ROW is filled with a table
        self.gb_dataspace.layout().addWidget(self.records)
        self.makeTable()


    def makeTable(self):
        """
        Makes and configures the records table.

        The records table describes the fields of a given `Table` leaf.

        :Parameters:

        - `records_desc`: a list of table record descriptions
        - `sect_labels`: a list with the labels of horizontal header sections
        """

        self.records.setNumRows(len(self.info['members']))
        self.records.setNumCols(3)

        # Fill the table
        # Use customised QTableItems that align cell content always to left
        row = 0
        for (name, dtype, shape) in self.info['members']:
            self.records.setItem(row, 0, VTTableItem(self.records,
                ro=True, text=name))
            self.records.setItem(row, 1, VTTableItem(self.records,
                ro=True, text=str(dtype)))
            self.records.setItem(row, 2, VTTableItem(self.records,
                ro=True, text=str(shape)))
            row = row + 1

        # Configure sizes
        self.records.resize(self.records.sizeHint())
        self.records.setColumnStretchable(0, True)
        self.records.setColumnStretchable(1, True)
        self.records.setColumnStretchable(2, True)

        # Set labels for horizontal sections
        hor_header = self.records.horizontalHeader()
        hor_header.setLabel(0, self.__tr('Field name',
            'First header section of the members table'))
        hor_header.setLabel(1, self.__tr('Type',
            'Second header section of the members table'))
        hor_header.setLabel(2, self.__tr('Shape',
            'Third header section of the members table'))

        # Hide vertical header
        self.records.verticalHeader().hide()
        self.records.setLeftMargin(0)

        # Give table a non editable look
        # By default tables' background is white and they look like an
        # editable widget
        self.records.setPaletteBackgroundColor(self.records.eraseColor())

        # Unbold the font
        font = self.font()
        font.setBold(0)
        self.records.viewport().setFont(font)

