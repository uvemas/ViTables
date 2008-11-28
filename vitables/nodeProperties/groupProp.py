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
#       $Id: groupProp.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the GroupGeneralPage class.

Classes:

* GroupGeneralPage(qt.QWidget)

Methods:

* __init__(self, info, root=False)
* __tr(self, source, comment=None)
* makeGeneralPage(self)
* makeTable(self, group_nodes, leaf_nodes)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt
import qttable

import vitables.utils
from vitables.vtWidgets.vtTableItem import VTTableItem

class GroupGeneralPage(qt.QWidget):
    """
    Makes the General page of groups properties dialog.

    The page has the following layout::

        root widget --> vbox layout
        database group box --> grid layout
            3*[labelName, labelValue, spacer]
        dataspace group box --> grid layout
            1*[labelName, labelValue, spacer]
            table
    """
    
    def __init__(self, info, root=False):
        """:Parameters:

        - `info`: a dictionary with the information to be displayed
        - `root`: indicates if the group is a root node or not
        """

        qt.QWidget.__init__(self)
        self.page_layout = qt.QVBoxLayout(self, 10, 6)

        self.info = info
        self.root = root

        if root:
            self.gb_dataspace = \
                qt.QGroupBox(self.__tr('Root group', 'Groupbox title'), self)
        else:
            self.gb_dataspace = \
                qt.QGroupBox(self.__tr('Group', 'Groupbox title'), self)
        nrows = int(self.info['members']) # number of children
        if nrows:
            self.children_table = qttable.QTable(self.gb_dataspace)
        self.makeGeneralPage()


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('GroupGeneralPage', source, comment).latin1()


    def makeGeneralPage(self):
        """Makes the ``General`` page."""

        #
        # Database is a GroupBox with grid layout #############################
        #

        gb_database = qt.QGroupBox(self.__tr('Database', 'Groupbox title'),
            self)
        gb_database.setOrientation(qt.Qt.Vertical)
        gb_database.setInsideMargin(10)
##        gb_database.setInsideSpacing(6) # Doesn't work, PyQt bug??
        gb_database.layout().setSpacing(6)

        # FIRST ROW Name: value
        name_label = qt.QLabel(self.__tr('Name:',
            'Label of the file/group name text box'), gb_database)
        vitables.utils.addRow(name_label, self.info['name'], gb_database)
        
        # SECOND ROW Path: value
        path_label = qt.QLabel(self.__tr('Path:',
            'Label of the file/group full path text box'), gb_database)
        vitables.utils.addRow(path_label, self.info['path'], gb_database)

        # THIRD ROW Type: value
        type_label = qt.QLabel(self.__tr('Type:',
            'Label of the type text box'), gb_database)
        vitables.utils.addRow(type_label, self.info['type'], gb_database)

        # FOURTH ROW Access mode: value
        if self.root:
            mode_label = qt.QLabel(self.__tr('Access mode:',
                'Label of the access mode text box'), gb_database)
            vitables.utils.addRow(mode_label, self.info['mode'], gb_database)

        # Adds the GroupBox to the General page layout
        self.page_layout.addWidget(gb_database)

        #
        # Dataspace is a GroupBox creation with a grid layout #################
        #
        self.gb_dataspace.setOrientation(qt.Qt.Vertical)
        self.gb_dataspace.setInsideMargin(10)
##        self.gb_dataspace.setInsideSpacing(6) # Doesn't work, PyQt bug??
        self.gb_dataspace.layout().setSpacing(6)

        # FIRST ROW ... children: value
        children_label = qt.QLabel( self.__tr('Number of children:',
            'Label of the group children text box'), self.gb_dataspace)
        vitables.utils.addRow(children_label, self.info['members'],
            self.gb_dataspace)

        # LAST ROW is filled with the group children table
        nrows = int(self.info['members']) # number of children
        if nrows:
            self.gb_dataspace.layout().addWidget(self.children_table)
            self.makeTable(self.info['groups'], self.info['leaves'])

        # Adds the GroupBox to the General page layout
        self.page_layout.addWidget(self.gb_dataspace)


    def makeTable(self, group_nodes, leaf_nodes):
        """
        Makes and configures the group's children table.

        Group children table has 2 columns: ``Name`` and ``Type``.

        :Parameters:

        - `group_nodes`: dict whose keys are the names of the children groups
        - `leaf_nodes`: dict whose keys are the names of the children leaves
        """

        self.children_table.setNumRows(int(self.info['members']))
        self.children_table.setNumCols(2)

        # The children groups list [(g1, 'Group'), (g2, 'Group'), ...]
        groups = [(name,
            self.__tr('Group',
                'Entry of the Type column of the group children table'))
            for name in group_nodes.keys()]

        # The children leaves list [(l1, 'Leaf'), (l2, 'Leaf'), ...]
        leaves = [(name,
            self.__tr('Leaf',
                'Entry of the Type column of the group children table'))
            for name in leaf_nodes.keys()]

        # Use customised QTableItems that align cell content always to left
        row = 0
        for (node_name, node_type) in groups + leaves:
            self.children_table.setItem(row, 0, VTTableItem(self.children_table,
                ro=True, text=node_name))
            self.children_table.setItem(row, 1, VTTableItem(self.children_table,
                ro=True, text=node_type))
            row = row + 1

        # Configure sizes
        self.children_table.resize(self.children_table.sizeHint())
        self.children_table.setColumnStretchable(0, True)
        self.children_table.setColumnStretchable(1, True)

        # Set labels for horizontal sections
        hor_header = self.children_table.horizontalHeader()
        hor_header.setLabel(0, self.__tr('Child name',
            'First column header of the group children table'))
        hor_header.setLabel(1, self.__tr('Type',
            'Second column header of the group children table'))

        # Hide vertical header
        self.children_table.verticalHeader().hide()
        self.children_table.setLeftMargin(0)

        # Give table a non editable look
        # By default tables' background is white and they look like an
        # editable widget
        self.children_table.setPaletteBackgroundColor(self.children_table.eraseColor())

        # Unbold the font
        font = self.font()
        font.setBold(0)
        self.children_table.viewport().setFont(font)

