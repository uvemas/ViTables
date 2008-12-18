# -*- coding: utf-8 -*-
#!/usr/bin/env python


########################################################################
#
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
#       $Id: leafView.py 1084 2008-11-13 11:45:16Z vmas $
#
########################################################################

"""
Here is defined the LeafView class.

Classes:

* LeafView(QtGui.QTreeView)

Methods:


Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import numpy

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

import vitables.vtTables.scrollBar as scrollBar
import vitables.nodes.nodeInfo as nodeInfo
import vitables.vtWidgets.zoomCell as zoomCell

class LeafView(QtGui.QTableView):
    """
    A view for real data contained in leaves.

    This is a customised view intended to deal with huge datasets.
    """

    def __init__(self, model, parent=None):
        """Create the view.

        :Parameters:

            - `model`: the model to be tied to this view
            - `parent`: the parent of the model
        """

        QtGui.QTableView.__init__(self, parent)
        self.setModel(model)
        self.model = model
        self.rbuffer = model.rbuffer
        self.leaf_numrows = self.rbuffer.leaf_numrows
        self.selection_model = self.selectionModel()
        self.current_cell = (None, None)

        # Setup the actual vertical scrollbar
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerItem)
        self.vscrollbar = self.verticalScrollBar()

        # For potentially huge datasets use a customised scrollbar
        if self.rbuffer.leaf_numrows > self.model.numrows:
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            self.tricky_vscrollbar = scrollBar.ScrollBar(self.vscrollbar)
            self.max_value = self.tricky_vscrollbar.maximum()
            self.tricky_vscrollbar.installEventFilter(self)

        # Setup the vertical header width
        #self.vheader = self.verticalHeader()
        self.vheader = QtGui.QHeaderView(QtCore.Qt.Vertical)
        self.setVerticalHeader(self.vheader)
        font = self.vheader.font()
        font.setBold(True)
        fmetrics = QtGui.QFontMetrics(font)
        max_width = fmetrics.width(" %s " % str(self.leaf_numrows))
        self.vheader.setMinimumWidth(max_width)
        self.vheader.setClickable(True)

        # Setup the headers' resize mode
        rmode = QtGui.QHeaderView.Stretch
        if self.model.columnCount() == 1:
            self.horizontalHeader().setResizeMode(rmode)
        if self.model.rowCount() == 1:
            self.vheader.setResizeMode(rmode)

        # Setup the text elide mode
        self.setTextElideMode(QtCore.Qt.ElideRight)

        # The DataSheet instance that contains this view
        self.data_sheet = None

        # Connect SIGNALS to slots
        self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self.zoomCell)
        if self.rbuffer.leaf_numrows > self.model.numrows:
            self.connect(self.tricky_vscrollbar, QtCore.SIGNAL("actionTriggered(int)"), self.navigateWithMouse)
            self.connect(self.selection_model, 
                        QtCore.SIGNAL("currentChanged(QModelIndex, QModelIndex)"), 
                        self.trackValidCurrentCell)
            self.connect(self.model, 
                        QtCore.SIGNAL("headerDataChanged(int, int, int)"), 
                        self.repaintCurrentCell)

    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(QtGui.qApp.translate('LeafView', source, comment))


    def syncView(self):
        """Syncronize the displayed data and the position of the visible
        vertical scrollbar.
        """

        top_left_corner = QtCore.QPoint(0, 0)
        fv_label = self.rbuffer.start + self.indexAt(top_left_corner).row() + 1
        value = numpy.array(fv_label*self.max_value/self.leaf_numrows, 
                            dtype=numpy.int64)
        self.tricky_vscrollbar.setValue(value)


    def eventFilter(self, widget, event):
        """Event handler that customises the LeafView behavior for some events.

        :Parameters:

            - `widget`: the widget that receives the event
            - `event`: the received event
        """

        if event.type() in (QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.Wheel):
            top_left = self.model.index(0, 0)
            bottom_right = self.model.index(self.model.numrows - 1, self.model.numcols - 1)
            self.dataChanged(top_left, bottom_right)
        return QtGui.QTableView.eventFilter(self, widget, event)


    def navigateWithMouse(self, int_action):
        """Navigate the table with the mouse.

        This method is called once the
        `action` has set the slider position but before the display has
        been updated (see documentation of the actionTriggered method in
        the Qt4 docs). For instance, if the action `move one line
        downwards` is received when the last section of the table is
        visible, a buffer fault will occur once the action gets propagated
        but, before it happens, this method is called giving us the chance
        of make a buffer update.

        :Parameter int_action: the triggered slider action
        """

        # actionTriggered() SIGNAL passes integer values but triggerAction()
        # method requires an argument from the QtGui.QAbstractSlider enum
        int2action = {1: QtGui.QAbstractSlider.SliderSingleStepAdd, 
                      2: QtGui.QAbstractSlider.SliderSingleStepSub, 
                      3: QtGui.QAbstractSlider.SliderPageStepAdd, 
                      4: QtGui.QAbstractSlider.SliderPageStepSub, 
                      7: QtGui.QAbstractSlider.SliderMove}
        if not int2action.has_key(int_action):
            return
        action = int2action[int_action]
        # Pass the action done in the visible scrollbar to the hidden scrollbar
        self.vscrollbar.triggerAction(action)
        # Check for buffer faults and synchronize displayed data and
        # visible vertical scrollbar
        if action in (QtGui.QAbstractSlider.SliderSingleStepAdd, 
            QtGui.QAbstractSlider.SliderPageStepAdd):
            self.addStep()
        elif action in (QtGui.QAbstractSlider.SliderSingleStepSub, 
            QtGui.QAbstractSlider.SliderPageStepSub):
            self.subStep()
        elif action == QtGui.QAbstractSlider.SliderMove:
            self.dragSlider()


    def addStep(self):
        """Move towards the last section line by line or page by page.
        """

        table_size = self.model.numrows
        last_section = self.rbuffer.start + table_size

        # The required offset to make the last section visible
        last_section_offset = self.vheader.length() - \
                                self.vheader.viewport().height()
        # If the last section is visible and it is not the last row of
        # the dataset then update the buffer
        if last_section_offset <= self.vheader.offset():
            if last_section < self.leaf_numrows:
                # Buffer fault. We read the next (contiguous) buffer
                start = self.rbuffer.start + table_size
                self.model.loadData(start, table_size)
                self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                                table_size - 1)
                self.scrollToTop()

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def subStep(self):
        """Move towards the first section line by line or page by page.
        """

        table_size = self.model.numrows
        first_section = self.rbuffer.start + 1

        # If the first section is visible and it is not the first row of
        # the dataset then update the buffer
        if self.vheader.offset() == 0:
            if first_section > 1:
                # Buffer fault. We read the previous (contiguous) buffer
                start = self.rbuffer.start - table_size
                self.model.loadData(start, table_size)
                self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                                table_size - 1)
                self.scrollToBottom()

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def dragSlider(self):
        """Move upward/downward the slider by dragging it or wheeling the mouse.

        When navigating large datasets we must beware that the number of
        rows of the dataset is greater than the number of values in the
        range of values of the scrollbar. It means that there are rows
        that cannot be reached with the scrollbar.

        The relationship between the scrollbar value and the row in the
        dataset can be expressed in several ways

        (max_value - value)/value = (numrows - row)/row
        row = (value * numrows)/max_value
        value = (row * max_value)/numrows
        """

        table_size = self.model.numrows

        value = self.tricky_vscrollbar.sliderPosition()
        if value == 0:
            row = 0
            self.vscrollbar.triggerAction(QtGui.QAbstractSlider.SliderToMinimum)
        elif value == self.tricky_vscrollbar.maximum():
            row = self.leaf_numrows - 1
            self.vscrollbar.triggerAction(QtGui.QAbstractSlider.SliderToMaximum)
        else:
            row = numpy.array(self.leaf_numrows*value/self.max_value, 
                              dtype=numpy.int64)
        # bottom dataset fault condition
        if row + table_size > self.leaf_numrows:
            start = self.leaf_numrows - table_size
        # top/bottom buffer fault condition
        elif (row < self.rbuffer.start) or \
            (row > self.rbuffer.start + table_size - 1):
            start = row - table_size/2
        # no fault condition occurs
        else:
            return
        self.model.loadData(start, table_size)
        self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                        table_size - 1)

    def keyPressEvent(self, event):
        """Handle basic cursor movement for key events.

        :Parameter event: the key event being processed.
        """

        if self.model.numrows < self.leaf_numrows:
            key = event.key()
            if key == QtCore.Qt.Key_Home:
                self.homeKeyPressEvent()
            elif key == QtCore.Qt.Key_End:
                self.endKeyPressEvent()
            elif key == QtCore.Qt.Key_Up:
                self.upKeyPressEvent(event)
            elif key == QtCore.Qt.Key_Down:
                self.downKeyPressEvent(event)
            elif key == QtCore.Qt.Key_PageUp:
                self.pageUpKeyPressEvent(event)
            elif key == QtCore.Qt.Key_PageDown:
                self.pageDownKeyPressEvent(event)
            else:
                QtGui.QTableView.keyPressEvent(self, event)
        else:
            QtGui.QTableView.keyPressEvent(self, event)


    def homeKeyPressEvent(self):
        """Specialised handler for the Home key press event.
        """

        current_column = self.vheader.currentIndex().column()

        # Update buffer if needed
        index = self.model.index(0, current_column)
        section = self.rbuffer.start + 1
        if section > 1:
            self.model.loadData(0, self.model.numrows)
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            self.model.numrows - 1)
        self.vheader.setCurrentIndex(index)
        self.scrollToTop()

        # Eventually synchronize the position of the visible scrollbar
        # the displayed data
        self.tricky_vscrollbar.setValue(0)


    def endKeyPressEvent(self):
        """Specialised handler for the End key press event.
        """

        current_column = self.vheader.currentIndex().column()
        table_size = self.model.numrows

        # Update buffer if needed
        index = self.model.index(table_size - 1, current_column)
        section = self.rbuffer.start + table_size
        if section < self.leaf_numrows:
            self.model.loadData(self.leaf_numrows - table_size, 
                                    table_size)
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            table_size - 1)
        self.vheader.setCurrentIndex(index)
        self.scrollToBottom()

        # Eventually synchronize the position of the visible scrollbar
        # the displayed data
        self.tricky_vscrollbar.setValue(self.max_value)


    def upKeyPressEvent(self, event):
        """Specialised handler for the cursor up key press event.

        :Parameter event: the key event being processed.
        """


        table_size = self.model.numrows

        # Replace the fake current cell with the valid current cell
        current_index = self.vheader.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadValidCurrentCell(buffer_row)
        buffer_start = self.rbuffer.start

        # If we are at the first row of the buffer but not at the first
        # row of the dataset we still can go upwards so we have to read
        # the previous contiguous buffer
        if (buffer_row == 0) and (buffer_start > 0):
            self.model.loadData(buffer_start - table_size, 
                                    table_size)
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            table_size - 1)
            # The position of the new current row
            # Beware that `buffer_start` is the first row of the OLD buffer
            if buffer_start - table_size < 0:
                row = int(buffer_start - 1)
            else:
                row = table_size - 1
            index = self.model.index(row, buffer_column)
            self.vheader.setCurrentIndex(index)
            self.scrollTo(index, QtGui.QAbstractItemView.PositionAtTop)
        else:
            QtGui.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()



    def pageUpKeyPressEvent(self, event):
        """Specialised handler for the PageUp key press event.

        :Parameter event: the key event being processed.
        """

        table_size = self.model.numrows
        page_step = self.vscrollbar.pageStep()

        # Replace the fake current cell with the valid current cell
        current_index = self.vheader.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadValidCurrentCell(buffer_row)
        dataset_row = self.rbuffer.start + buffer_row
        old_buffer_start = self.rbuffer.start

        # If we are at the first page of the buffer but not at the first
        # page of the dataset we still can go upwards so we have to read
        # the previous contiguous buffer
        if (buffer_row - page_step < 0) and (self.rbuffer.start > 0):
            self.model.loadData(old_buffer_start - table_size, 
                                    table_size)
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            table_size - 1)
            # The position of the new current row
            row = int(dataset_row - page_step - self.rbuffer.start)
            if row < 0:
                row = 0
            index = self.model.index(row, buffer_column)
            self.vheader.setCurrentIndex(index)
            self.scrollTo(index, QtGui.QAbstractItemView.PositionAtTop)
        else:
            QtGui.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()



    def downKeyPressEvent(self, event):
        """Specialised handler for the cursor down key press event.

        :Parameter event: the key event being processed.
        """

        table_size = self.model.numrows

        # Replace the fake current cell with the valid current cell
        current_index = self.vheader.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadValidCurrentCell(buffer_row)
        dataset_row = self.rbuffer.start + buffer_row
        buffer_end = self.rbuffer.start + table_size - 1

        # If we are at the last row of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (buffer_row == table_size - 1) and \
            (self.rbuffer.start + table_size < self.leaf_numrows):
            self.model.loadData(buffer_end + 1, table_size)
            # The position of the new current row
            # Beware that `buffer_end` is the last row of the OLD buffer
            if buffer_end + table_size > self.leaf_numrows - 1:
                row = int(dataset_row - self.rbuffer.start + 1)
            else:
                row = 0
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            table_size - 1)
            index = self.model.index(row, buffer_column)
            self.vheader.setCurrentIndex(index)
            self.scrollTo(index, QtGui.QAbstractItemView.PositionAtBottom)
        else:
            QtGui.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()



    def pageDownKeyPressEvent(self, event):
        """Specialised handler for the PageDown key press event.

        :Parameter event: the key event being processed.
        """

        table_size = self.rbuffer.chunk_size
        page_step = self.vscrollbar.pageStep()

        # Replace the fake current cell with the valid current cell
        current_index = self.vheader.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadValidCurrentCell(buffer_row)
        dataset_row = self.rbuffer.start + buffer_row
        old_buffer_end = self.rbuffer.start + table_size - 1

        # If we are at the last page of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (buffer_row + page_step > table_size - 1) and \
            (self.rbuffer.start + table_size < self.leaf_numrows):
            self.model.loadData(dataset_row + 1, table_size)
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            table_size - 1)
            # The position of the new current row
            row = dataset_row - self.rbuffer.start + page_step
            if row > table_size - 1:
                row = table_size - 1
            index = self.model.index(row, buffer_column)
            self.vheader.setCurrentIndex(index)
            self.scrollTo(index, QtGui.QAbstractItemView.PositionAtBottom)
        else:
            QtGui.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()



    def wheelEvent(self, event):
        """Send the wheel events received by the viewport to the visible
        vertical scrollbar.
        """

        if self.rbuffer.leaf_numrows > self.model.numrows:
            QtCore.QCoreApplication.sendEvent(self.tricky_vscrollbar, event)
        else:
            QtGui.QTableView.wheelEvent(self, event)


    # For large datasets the number of rows of the dataset is greater than
    # the number of rows of the table used for displaying data. It means
    # that if a table cell is activated (made selected by clicking, double
    # cliking or pressing the arrow keys. We call this cell *valid current
    # cell*) we must take care for keeping it updated. For instance, if
    # the table contains the first 10000 rows of the dataset and the user
    # clicks the cell (52, 1) it becomes the valid current cell. If now the
    # user draggs the slider and goes down let say 30000 rows then the row
    # 52 of the table will still be the current one but its section number
    # will be 30052 which is wrong (the current cell can only be changed by
    # activating other cell, not by dragging the scrollbar). We call this
    # cell *fake current cell*. This would be a bug. The following code
    # avoids it.


    def trackValidCurrentCell(self, current, previous):
        """Track the valid current cell.

        :Parameters:

            -`current`: the model index of the new current cell
            -`previous`: the model index of the previous current cell
        """
        self.current_cell = (self.rbuffer.start + current.row() + 1, 
                            current.column())

    def repaintCurrentCell(self):
        """Repaint the current cell if needed.

        This method is called every time the vertical header is updated. As
        we force an update of that header every time the buffer is reloaded
        this method is used to repaint the current cell every time the
        buffer is reloaded.
        """

        current_index = self.currentIndex()
        if not current_index.isValid():
            return

        current_section = self.rbuffer.start + current_index.row() + 1
        if (current_section, current_index.column()) == self.current_cell:
            # The cell is the valid current cell
            self.selection_model.select(current_index, 
                                    QtGui.QItemSelectionModel.SelectCurrent)
        else:
            # The cell is a fake current cell
            self.selection_model.clearSelection()


    def loadValidCurrentCell(self, row):
        """Load the buffer in which the valid current cell lives.

        :Parameter row: the position of the valid current cell in the model
        """

        table_size = self.model.numrows
        current_section = self.current_cell[0]
        current_column = self.current_cell[1]
        if not current_section in (self.rbuffer.start, 
            self.rbuffer.start + table_size):
            self.model.loadData(current_section - row - 1, table_size)
            self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, 
                                            table_size - 1)

    def zoomCell(self, index):
        """Display the inner dimensions of a cell.

        :Parameter index: the model index of the cell being zoomed
        """

        row = index.row()
        column = index.column()
        data = self.rbuffer.getCell(row, column)

        # The title of the zoomed view
        node = self.data_sheet.leaf
        info = nodeInfo.NodeInfo(node)
        if node.node_kind == 'table':
            col = info.columns_names[column]
            title = '%s: %s[%s]' % (node.name, col, row + 1)
        else:
            title = '%s: (%s,%s)' % (node.name, row + 1, column + 1)

        zoomCell.ZoomCell(data, title, self.data_sheet.vtapp.workspace, 
                          self.data_sheet.leaf)


