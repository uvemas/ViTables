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
#       $Id: leafView.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the LeafView class.

Classes:

* LeafView(qt.QObject)

Methods:

* __init__(self,  lvitem, max_rows, doc, rows, cols, parent)
* __tr(self, source, comment=None)
* configTable(self)
* addInfoButton(self)
* updateInfoTooltip(self)
* slotViewProperties(self)
* slotZoomView(self, row, col, button, position)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt

import vitables.utils
import vitables.vtTables. hpTable as vthpt
import vitables.vtWidgets.zoomCell as vtw

class LeafView(qt.QObject):


    def __init__(self,  lvitem, max_rows, doc, rows, cols, parent):
        """
        Create a view that displays the data contained in a given leaf
        (table or array).

        This class represents the view and it is binded to a model (an open
        leaf). Model and view are controlled by the leaves manager.

        :Parameters:

        - `lvitem`: the tree view item being displayed
        - `max_rows`: the size criterium for datasets
        - `doc`: the document we want to show (an instance of `NodeDoc` class)
        - `rows`: the number of rows of the view
        - `cols`: the number of columns of the view
        - `parent`: the application workspace
        """

        # The tree view item being displayed
        self.lvitem = lvitem

        # The document being displayed
        self.doc = doc

        # The parent widget is the application workspace
        self.workspace = parent

        qt.QObject.__init__(self)

        # The table widget where the view is displayed
        self.hp_table = vthpt.HPTable(self.doc, max_rows, rows, cols, parent, 
            self)

        #
        # View configuration
        #
        self.configTable()
        self.info_button = qt.QPushButton('', self.hp_table.hpViewport)
        self.addInfoButton()

        #
        # Connect qt.SIGNALs to slots
        #

        self.connect(self.info_button, qt.SIGNAL('clicked()'),
            self.slotViewProperties)
        self.connect(self.hp_table.hpViewport,
            qt.SIGNAL('doubleClicked(int, int, int, const QPoint &)'),
                self.slotZoomView)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('LeafView', source, comment).latin1()


    def configTable(self):
        """
        Configure titlebar and headers of the view.

        The `X11` server adds a frame to the view widget (unless the flag
        `WX11BypassWM` is passed to the widget constructor), and this
        frame is decorated by the window manager. The titlebar can be
        customized through setIcon methods (they set the top left corner
        icon of the frame).
        """

        # The viewport component of the hpTable
        viewport = self.hp_table.hpViewport

        # The icons dictionary
        icons = vitables.utils.getIcons()

        #
        # Configure the titlebar ##############################################
        #

        # Setup the window caption
        caption = '%s  %s' % (self.doc.getNodeName(),
            self.doc.nodeTitle())
        self.hp_table.setCaption(caption)

        type2iconname = {'Table': 'table', 'EArray': 'earray',
            'CArray': 'carray', 'Array': 'array', 'VLArray': 'vlarray',
            'VLString': 'vlstring', 'Object': 'object'}
        leaf_type = self.doc.getNodeInfo()['type']
        
        if leaf_type == 'VLArray':
            # Support for both PyTables format version 1.x (in which
            # flavor can be VLString and Object) and PyTables format
            # version 2.x (in which those values are obsolete and the
            # PSEUDOATOM attribute has been introduced)
            flavor = self.doc.getFlavor()
            attrs = self.doc.getASI()
            if hasattr(attrs, 'PSEUDOATOM'):
                pseudoatom = attrs.PSEUDOATOM
            else:
                pseudoatom = None
            if (flavor == 'VLString') or (pseudoatom == 'vlstring'):
                leaf_type = 'VLString'
            elif (flavor == 'Object') or (pseudoatom == 'object'):
                leaf_type = 'Object'

        self.hp_table.setIcon(icons[type2iconname[leaf_type]].pixmap(\
            qt.QIconSet.Small, qt.QIconSet.Normal, qt.QIconSet.On))

        #
        # Configure horizontal header #########################################
        #
        col_header = viewport.horizontalHeader()

        # Rename sections
        if leaf_type == 'Table':
            colnames = self.doc.tableColumnsNames()
            for i in range(len(colnames)):
                # If the column is nested
                if isinstance(colnames[i], tuple):
                    name = colnames[i][0]
                else:
                    name = colnames[i]
                col_header.setLabel(i, name)

        #
        # Configure vertical header ###########################################
        #
        # Ensures that even the widest labels can be displayed
        widest_string = 'W%sWW' % self.doc.numRows()
        header_width = qt.qApp.fontMetrics().width(widest_string)

        # Ensures that the info button will have room enough
        if header_width < 22:
            header_width = 22
        viewport.setLeftMargin(header_width)

        #
        # Setup other properties ##############################################
        #
        viewport.setReadOnly(1)
        if self.doc.numCols() == 1:
            # Force the column width and the frame width to be the same
            # i.e forces the horizontal header width and frame witdh to
            # be the same
            viewport.setColumnStretchable(0, 1)


    def addInfoButton(self):
        """Attaches an info icon to the top left corner of the table."""

        # The icons dictionary
        icons = vitables.utils.getIcons()

        # Create and configure...
        hp_table = self.hp_table.hpViewport

        self.info_button.setPixmap(icons['info'].pixmap(qt.QIconSet.Small,
            qt.QIconSet.Normal, qt.QIconSet.On))

        self.info_button.setFlat(0)
        button_height = hp_table.horizontalHeader().height() - 2
        button_width = hp_table.verticalHeader().width() - 2
        self.info_button.setGeometry(2, 2, button_width, button_height)
        self.updateInfoTooltip()


    def updateInfoTooltip(self):
        """Setup the tooltip text for the info button."""

        # The escape method returns None if node_title is an empty string
        node_title = qt.QStyleSheet.escape(self.doc.nodeTitle()).latin1()
        info_text =  self.__tr("""<strong>File:</strong> %s<br>""" 
            """<strong>Path:</strong> %s<br>"""
            """<strong>Title:</strong> %s<br>"""
            """<strong>Shape: </strong> %s""",
            'Part of the leaf info tooltip') % (self.doc.filepath,
                self.doc.nodepath, node_title, self.doc.getShape())
        qt.QToolTip.add(self.info_button, info_text)


    def slotViewProperties(self):
        """
        Displays the properties dialog for the currently selected node.

        When the info button is clicked it emits a `qt.SIGNAL` that is
        connected to this slot. It triggers a `qt.PYSIGNAL` that should
        be captured by the leaves manager and connected to the proper
        slot.
        """
        self.emit(qt.PYSIGNAL('infoButtonClicked(DBDoc, TreeNode)'),
            (self.doc.dbdoc, self.lvitem,))


    def slotZoomView(self, row, col, button, position):
        """
        Makes the content of a cell fully visible.

        If we are displaying a leaf with more than 2 dimensions, then
        theleft clicked cell is displayed in its own tabular view (it
        is zoomed).

        :Parameters:

        - `row`: the row of the clicked cell
        - `col`: the zv_col of the clicked cell
        - `button`: the mouse button pressed
        - `position`: the mouse position (not used)
        """
        if row < 0:
            # Do nothing if we click on an empty table/array
            return

        table = self.hp_table.hpViewport
        # Check if the zoom has to be done
        if button == qt.Qt.LeftButton:
            # Get the zv_col ID to be used in the view caption
            if self.doc.isInstanceOf('Table'):
                zv_col = table.horizontalHeader().label(col)
            else:
                zv_col = col + 1
            # Get the row ID to be used in the view caption
            # The view has at most 1000 rows. We need to convert the
            # view number of row into the document number of row
            docRow = table.getRowLabel(row) - 1
            zv_row = docRow + 1
            # Make the caption
            if self.doc.isInstanceOf('Table'):
                caption = '%s: %s[%s]' % (self.doc.getNodeName(), zv_col,
                    zv_row)
            else:
                caption = '%s: (%s, %s)' % (self.doc.getNodeName(), zv_row,
                    zv_col)
            # Get the cell content
            cell = self.doc.getCell(docRow, col)
            vtw.ZoomCell(cell, caption, self.workspace)
        else:
            pass
