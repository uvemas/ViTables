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
#       $Id: hpTable.py 1019 2008-03-28 12:26:43Z vmas $
#
########################################################################

"""Here is defined the HPTable class.

Classes:

* HPTable(qt.QWidget)

Methods:

* __init__(self,  doc, maxRows, numRows, numCols, workspace, leaf_view)
* __tr(self, source, comment=None)
* configureRowCounter(self)
* slotShowRowCounter(self)
* slotHideRowCounter(self)
* slotUpdateRowCounter(self, value)
* syncTable(self)
* syncScrollBar(self, value)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import locale

import numpy

import qt

from vitables.vtTables.hpScrollBar import HPScrollBar
from vitables.vtTables.hpViewport import HPViewport

class HPTable(qt.QWidget):


    def __init__(self,  doc, maxRows, numRows, numCols, workspace, leaf_view):
        """
        Create a view that displays the data contained in a given
        leaf (table or array).

        This class represents the view and it is binded to a model (an
        open leaf). Model and view are controlled by the leaves manager.

        :Parameters:

        - `doc`: the document we want to show (an instance of NodeDoc class)
        - `maxRows`: the size criterium for datasets
        - `numRows`: the number of rows of the view
        - `numCols`: the number of columns of the view
        - `workspace`: the application workspace
        - `leaf_view`: the LeafView object tied to this widget
        """

        # The document being displayed
        self.doc = doc

        # Create the widget that will contain the high performance table
        # QWidget.WDestructiveClose causes that, when the frame close
        # button is clicked, the widget is hiden AND destroyed --> the
        # workspace updates automatically its list of open windows -->
        # the Windows menu content is automatically updated
        #
        # HPTable parent is the workspace
        qt.QWidget.__init__(self, workspace)
        flags = qt.QWidget.WDestructiveClose
        self.setWFlags(flags)

        # This is attribute comes in handy for synchronizing workspace
        # and tree view pane, see VTApp.slotSynchronizeTreeView method.
        self.leaf_view = leaf_view

        #
        # Compose the High Performance Table
        #
        self.hpViewport = HPViewport(self.doc, numRows, numCols, self)
        self.hpScrollBar = HPScrollBar(self)

        # Put all components together
        hpLayout = qt.QHBoxLayout(self)
        hpLayout.addWidget(self.hpViewport)
        hpLayout.addWidget(self.hpScrollBar)


        #
        # Scrollbar choice
        #

        if numRows >= maxRows:
            # The scrollbar of hpTable is always hiden, hpScrollBar is visible
            self.hpViewport.setVScrollBarMode(qt.QScrollView.AlwaysOff)
            self.hpScrollBar.show()

            # Components synchronization
            self.connect(self.hpViewport.verticalScrollBar(),
                qt.SIGNAL('valueChanged(int)'), self.syncScrollBar)
            self.connect(self.hpScrollBar, qt.SIGNAL('sliderReleased()'),
                self.syncTable)

        else:
            # The hpScrollBar is hiden, the scrollbar of hpViewport is not
            self.hpScrollBar.hide()

        self.resize(300, 200)

        # The row indicator
        self.rowCounter = qt.QLabel(self)
        self.configureRowCounter()

        #
        # Connect signals to slots
        #

        # Row counter
        self.connect(self.hpScrollBar, qt.SIGNAL('sliderPressed()'),
            self.slotShowRowCounter)
        self.connect(self.hpScrollBar, qt.SIGNAL('sliderReleased()'),
            self.slotHideRowCounter)
        self.connect(self.hpScrollBar, qt.SIGNAL('sliderMoved(int)'),
            self.slotUpdateRowCounter)

        # Scrollbar navigation
        self.connect(self.hpScrollBar, qt.SIGNAL('nextLine()'),
            self.hpViewport.nextLine)
        self.connect(self.hpScrollBar, qt.SIGNAL('prevLine()'),
            self.hpViewport.prevLine)
        self.connect(self.hpScrollBar, qt.SIGNAL('nextPage()'),
            self.hpViewport.nextPage)
        self.connect(self.hpScrollBar, qt.SIGNAL('prevPage()'),
            self.hpViewport.prevPage)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('HPTable', source, comment).latin1()


    def configureRowCounter(self):
        """
        Initializes the label that will display the number of row
        corresponding to the current scrollbar value when the user
        drags the slider.

        The row counter will only be displayed in tables whose
        scrollbar is an instance of HPScrollBar, i.e in large tables.
        """

        # The label will only be visible when the user presses/drags the slider
        self.rowCounter.hide()

        # The label will look like a decorated tooltip
        p = qt.QToolTip.palette()
        self.rowCounter.setPalette(p)
        self.rowCounter.setLineWidth(2)
        self.rowCounter.setFrameStyle(qt.QFrame.Raised | qt.QFrame.StyledPanel)

        # Contents are boldfaced
        f = self.rowCounter.font()
        f.setBold(True)
        self.rowCounter.setFont(f)


    def slotShowRowCounter(self):
        """
        Shows the row counter when the slider is pressed.

        The row counter will only be displayed in tables whose scrollbar
        is an instance of HPScrollBar, i.e in large tables, and will
        remain visible until the user releases the slider.
        """

        # The current slider value
        v = self.hpScrollBar.value()

        # Show the row indicator label
        self.slotUpdateRowCounter(v)
        self.rowCounter.show()


    def slotHideRowCounter(self):
        """Hides the row counter when the user releases the slider."""
        self.rowCounter.hide()


    def slotUpdateRowCounter(self, value):
        """
        Updates the contents and position of the row counter.

        This method doesn't change the visibility of the row counter.

        :Parameter value: the scrollbar value
        """

        # The pointed row
        row = 1.0 * value * self.doc.numRows()/self.hpScrollBar.maxValue() + 1
        row = min(self.doc.numRows(), row)
        # Format the row value according to the current locale
        rowLabel = locale.format('%s', long(row), 1)

        # The displayed text
        labelText = self.__tr('Row: ', 'The row indicator text')
        text = "".join([labelText, rowLabel])

        # Display the row position info
        self.rowCounter.setText(text)

        # The row indicator is displayed next to the slider
        self.rowCounter.adjustSize()
        y = self.hpScrollBar.sliderRect().y()
        x = self.width() - self.rowCounter.width() - 20
        self.rowCounter.move(x, y)
        self.rowCounter.repaint()


    def syncTable(self):
        """
        Syncrhonizes the viewport and the scrollbar components.

        The method is called every time the user releases the slider
        of the fake scrollbar. It updates the viewport according to
        the new slider position.

        This slot is not connected to the SIGNAL valueChanged(int) of
        the scrollbar for performance reasons: it would slow down the
        navigation speed when the slider is dragged). Our approach is to
        use a row indicator when the slider is being dragged, and update
        the table contents when the slider is released.
        """

        # Disconnect is necessary: syncTable --> setContentsPos/ensureVisible
        # methods called --> real scrollbar value changed --> syncScrollBar
        self.disconnect(self.hpViewport.sb, qt.SIGNAL('valueChanged(int)'),
            self.syncScrollBar)

        # The viewport and scrollbar components
        viewport = self.hpViewport
        scrollBar = self.hpScrollBar

        # The number of visible rows
        page = viewport.getPageSize()

        # Synchronizes the contents displayed in the viewport
        # component with the value of the scrollbar component
        v = scrollBar.value()
        if v== 0:
            # Displays doc home at table home (cannot call goHome
            # because it sets the current cell) preserving the column
            viewport.setContentsPos(viewport.contentsX(), 0)
            viewport.firstRowLabel = 1
            viewport.tableFault(viewport.firstRowLabel)
        elif v == scrollBar.maxValue():
            # Displays doc end at table end (cannot call goEnd because
            # it sets the current cell) preserving the column
            viewport.ensureVisible(viewport.contentsX(),
                viewport.contentsHeight())
            viewport.firstRowLabel = self.doc.numRows() - viewport.tableLength + 1
            viewport.tableFault(viewport.firstRowLabel)
        else:
            # Displays doc row docIndex at table row with position y,
            # preserving the column
            y = 1.0 * v * viewport.contentsHeight()/scrollBar.maxValue()
            viewport.ensureVisible(viewport.contentsX(), y)
            # Direct ratio: docRow/docLength = v/max
            docIndex = v * self.doc.numRows() / scrollBar.maxValue()
            viewport.firstRowLabel = docIndex - viewport.rowAt(int(y)) + 1
            viewport.tableFault(viewport.firstRowLabel)

        self.connect(self.hpViewport.sb, qt.SIGNAL('valueChanged(int)'),
            self.syncScrollBar)


    def syncScrollBar(self, value):
        """
        Slot that syncronizes the viewport and the scrollbar.

        The method is called every time the user navigates the table
        either by hand (with the keyboard or the mouse wheel) or
        programmatically (for instance via methods setContentsPos or
        ensureVisible). It updates the position of the fake
        scrollbar slider according to the viewport.

        This slot is connected to the valueChanged SIGNAL in the
        HPViewport instance. The parameter passed by the signal is
        not really needed, so it is not processed in any way.

        :Parameter value: the hidden scrollbar value
        """

        # The number of visible rows
        page = self.hpViewport.getPageSize()

        # The index in the document of the first displayed row
        topSection = \
            self.hpViewport.rowsHeader.sectionAt(self.hpViewport.contentsY())
        topLabel = self.hpViewport.rowsHeader.label(topSection).latin1()
        # The real row index must be an int64 in order to address
        # spaces with more than 2**32 bits
        topLabel = numpy.array(topLabel).astype(numpy.int64)
        docTopIndex = topLabel - 1
        if docTopIndex== 0:
            # We are home
            v = 0
        elif docTopIndex > self.doc.numRows() - page:
            # We are at the end
            v = self.hpScrollBar.maxValue()
        else:
            # We are in the middle
            # Direct ratio: docRow/docLength = v/max
            v = self.hpScrollBar.maxValue() * docTopIndex / self.doc.numRows()

        # Set the scrollbar value
        self.hpScrollBar.setValue(v)
