# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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

"""
This module defines a view for the model bound to a `tables.Leaf` node.

This view is used to display the real data stored in a `tables.Leaf` node in a
tabular way:

    - scalar arrays are displayed in a 1x1 table.
    - 1D arrays are displayed in a Mx1 table.
    - KD arrays are displayed in a MxN table.
    - tables are displayed in a MxN table with one field per column

"""

__docformat__ = 'restructuredtext'

import numpy

from PyQt4 import QtCore, QtGui

import vitables.vtTables.scrollBar as scrollBar

class LeafView(QtGui.QTableView):
    """
    A view for real data contained in leaves.

    This is a customised view intended to deal with huge datasets.

    :Parameters:

    - `tmodel`: the leaf model to be tied to this view
    - `parent`: the parent of this widget
    """

    def __init__(self, tmodel, parent=None):
        """Create the view.
        """

        super(LeafView, self).__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setModel(tmodel)
        self.tmodel = tmodel  # This is a MUST
        self.leaf_numrows = self.tmodel.rbuffer.leaf_numrows
        self.selection_model = self.selectionModel()
        self.current_cell = (None, None)

        # Setup the actual vertical scrollbar
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerItem)
        self.vscrollbar = self.verticalScrollBar()

        # For potentially huge datasets use a customised scrollbar
        if self.leaf_numrows > self.tmodel.numrows:
            self.rbuffer_fault = False
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            self.tricky_vscrollbar = scrollBar.ScrollBar(self)
            self.max_value = self.tvsMaxValue()
            self.tricky_vscrollbar.setMaximum(self.max_value)
            self.tricky_vscrollbar.setMinimum(0)
            self.interval_size = self.mapSlider2Leaf()

        # Setup the vertical header width
        self.vheader = QtGui.QHeaderView(QtCore.Qt.Vertical)
        self.setVerticalHeader(self.vheader)
        font = self.vheader.font()
        font.setBold(True)
        fmetrics = QtGui.QFontMetrics(font)
        max_width = fmetrics.width(u" {0} ".format(unicode(self.leaf_numrows)))
        self.vheader.setMinimumWidth(max_width)
        self.vheader.setClickable(True)

        # Setup the headers' resize mode
        rmode = QtGui.QHeaderView.Stretch
        if self.tmodel.columnCount() == 1:
            self.horizontalHeader().setResizeMode(rmode)
        if self.tmodel.rowCount() == 1:
            self.vheader.setResizeMode(rmode)

        # Setup the text elide mode
        self.setTextElideMode(QtCore.Qt.ElideRight)

        # Connect signals to slots
        if self.leaf_numrows > self.tmodel.numrows:
            self.tricky_vscrollbar.actionTriggered.connect(\
                self.navigateWithMouse)


    def tvsMaxValue(self):
        """Calulate the maximum range value of the tricky vertical scrollbar.
        """

        # The scrollbar range must be a signed 32 bits integer so its
        # largest range is [0, 2**31 - 1]
        top_value = 2**31 - 1
        if self.leaf_numrows <= top_value:
            top_value = self.leaf_numrows
        return top_value



    def mapSlider2Leaf(self):
        """Map the slider position a row in the leaf.

        We divide the number of rows into equaly sized intervals. The
        interval size is given by the formula::

            int(self.leaf_numrows/self.max_value)

        Note that the larger is the number of rows the worse is this
        approach. In the worst case we would have an interval size of
        (2**64 - 1)/(2**31 - 1) = 2**33. Nevertheless the approach is
        quite good for number of rows about 2**33 (eight thousand million
        rows). In this case the interval size is about 4.
        """

        # If the slider range equals to the number of rows of the dataset
        # then there is a 1:1 mapping between range values and dataset
        # rows and row equals to value
        interval_size = 1
        if self.max_value < self.leaf_numrows:
            interval_size = int(self.leaf_numrows/self.max_value)
        return interval_size


    def syncView(self):
        """Update the tricky scrollbar value accordingly to first visible row.
        """

        top_left_corner = QtCore.QPoint(0, 0)
        # The first visible label
        fv_label = \
            self.tmodel.rbuffer.start + self.indexAt(top_left_corner).row() + 1
        value = numpy.rint(numpy.array(fv_label/self.interval_size, 
            dtype=numpy.float64))
        self.tricky_vscrollbar.setValue(value)


    def updateView(self):
        """Update the view contents after a buffer fault.
        """

        table_size = self.tmodel.numrows
    #    self.vheader.headerDataChanged(QtCore.Qt.Vertical, 0, table_size - 1)
        top_left = self.tmodel.index(0, 0)
        bottom_right = self.tmodel.index(self.tmodel.numrows - 1, 
                                            self.tmodel.numcols - 1)
        self.dataChanged(top_left, bottom_right)


    def navigateWithMouse(self, action):
        """Navigate the view with the mouse.

        This slot is called after the `action` has set the slider position 
        but before the display has been updated (see documentation of the 
        QAbstractSlider.actionTriggered signal in the Qt4 docs). So in this 
        method we can safely do any action before that display update happens. 
        For instance, if the received action is `move one line downwards` and 
        the last section of the table is visible, we can make a buffer update, 
        realize than a buffer fault is needed and do it. After executing this 
        slot the valueChanged signal will be emitted and the visual display 
        will be updated.

        :Parameter action: the triggered slider action
        """

        # The QAbstractSlider.SliderAction enum values used in this method
        # QtGui.QAbstractSlider.SliderSingleStepAdd -> 1
        # QtGui.QAbstractSlider.SliderSingleStepSub -> 2
        # QtGui.QAbstractSlider.SliderPageStepAdd -> 3
        # QtGui.QAbstractSlider.SliderPageStepSub -> 4
        # QtGui.QAbstractSlider.SliderMove -> 7
        if not action in (1, 2, 3, 4, 7):
            return
        # Pass the action done in the visible scrollbar to the hidden scrollbar
        self.vscrollbar.triggerAction(action)
        # Check for buffer faults and synchronize displayed data and
        # visible vertical scrollbar
        if action in (1, 3): 
            self.addStep()
        elif action in (2, 4):
            self.subStep()
        elif action == 7:
            # The slider is being dragged or wheeled
            self.dragSlider()


    def addStep(self):
        """Move towards the last section line by line or page by page.
        """

        table_size = self.tmodel.numrows
        last_section = self.tmodel.rbuffer.start + table_size

        # The required offset to make the last section visible i.e where
        # should start the viewport to ensure that the last section is
        # visible
        last_section_offset = self.vheader.length() - \
                                self.vheader.viewport().height()
        # If the last section is visible and it is not the last row of
        # the dataset then update the buffer
        if last_section_offset <= self.vheader.offset():
            if last_section < self.leaf_numrows:
                # Buffer fault. We read the next (contiguous) buffer
                start = self.tmodel.rbuffer.start + table_size
                self.tmodel.loadData(start, table_size)
                self.updateView()
                self.scrollToTop()

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def subStep(self):
        """Move towards the first section line by line or page by page.
        """

        table_size = self.tmodel.numrows
        first_section = self.tmodel.rbuffer.start + 1

        # If the first section is visible and it is not the first row of
        # the dataset then update the buffer
        if self.vheader.offset() == 0:
            if first_section > 1:
                # Buffer fault. We read the previous (contiguous) buffer
                start = self.tmodel.rbuffer.start - table_size
                self.tmodel.loadData(start, table_size)
                self.updateView()
                self.scrollToBottom()

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def dragSlider(self):
        """Move the slider by dragging it or wheeling the mouse.

        When navigating large datasets we must beware that the number of
        rows of the dataset (uint64) is greater than the number of
        values in the range of values (int32) of the scrollbar. It means
        that there are rows that cannot be reached with the scrollbar.

        Note:: QScrollBar.sliderPosition and QScrollBar.value not always
        return the same value. When we reache the top of the dataset:

        - wheeling: value() returns 0, sliderPosition() returns a
            negative number
        - dragging: sliderPosition() returns 0, value() returns values
            larger than 0
        """

        table_size = self.tmodel.numrows
        value = self.tricky_vscrollbar.sliderPosition()
        if value < 0:
            value = 0
        if value > self.max_value:
            value = self.max_value
        row = numpy.array(self.interval_size*value, dtype=numpy.int64)

        # top buffer fault condition
        if row < self.tmodel.rbuffer.start:
            self.topBF(value, row)
        # bottom buffer fault condition
        elif row > self.tmodel.rbuffer.start + table_size:
            self.bottomBF(value, row)
        # We are at top of the dataset
        elif value == self.tricky_vscrollbar.minimum():
            self.topDataset()
        # We are at bottom of the dataset
        elif value == self.tricky_vscrollbar.maximum():
            self.bottomDataset()
        # no fault condition occurs
        else:
            position = row - self.tmodel.rbuffer.start
            index = self.tmodel.index(position, 0)
            self.scrollTo(index, QtGui.QAbstractItemView.PositionAtTop)


    def topBF(self, value, row):
        """Going out of buffer when browsing upwards.

        Buffer fault condition: row < rbuffer.start

        :Parameters:

            - `value`: the current value of the tricky scrollbar
            - `row`: the estimated dataset row mapped to that value
        """

        table_size = self.tmodel.numrows
        if value == self.tricky_vscrollbar.minimum():
            row = 0
            start = 0
            position = 0
            hint = QtGui.QAbstractItemView.PositionAtTop
            self.vscrollbar.triggerAction(\
                QtGui.QAbstractSlider.SliderToMinimum)
        else:
            start = row - table_size
            position = table_size - 1
            hint = QtGui.QAbstractItemView.PositionAtBottom

        self.tmodel.loadData(start, table_size)
        self.updateView()
        index = self.tmodel.index(position, 0)
        self.scrollTo(index, hint)


    def bottomBF(self, value, row):
        """Going out of buffer when browsing downwards.

        Buffer fault condition: row > self.tmodel.rbuffer.start + table_size - 1

        :Parameters:

            - `value`: the current value of the tricky scrollbar
            - `row`: the estimated dataset row mapped to that value
        """

        table_size = self.tmodel.numrows
        if value == self.tricky_vscrollbar.maximum():
            row = self.leaf_numrows - 1
            start = self.leaf_numrows - table_size
            position = table_size - 1
            hint = QtGui.QAbstractItemView.PositionAtBottom
            self.vscrollbar.triggerAction(\
                QtGui.QAbstractSlider.SliderToMinimum)
        else:
            start = row
            position = row - start
            hint = QtGui.QAbstractItemView.PositionAtTop

        self.tmodel.loadData(start, table_size)
        self.updateView()
        index = self.tmodel.index(position, 0)
        self.scrollTo(index, hint)


    def topDataset(self):
        """First dataset row reached with no buffer fault.
        """

        position = 0
        hint = QtGui.QAbstractItemView.EnsureVisible
        self.vscrollbar.triggerAction(\
            QtGui.QAbstractSlider.SliderToMinimum)
        index = self.tmodel.index(position, 0)
        self.scrollTo(index, hint)


    def bottomDataset(self):
        """Last dataset row reached with no buffer fault.
        """

        table_size = self.tmodel.numrows
        position = table_size - 1
        hint = QtGui.QAbstractItemView.EnsureVisible
        self.vscrollbar.triggerAction(\
            QtGui.QAbstractSlider.SliderToMaximum)
        index = self.tmodel.index(position, 0)
        self.scrollTo(index, hint)


    def wheelEvent(self, event):
        """Send the wheel events received by the *viewport* to the visible
        vertical scrollbar.

        :Parameter event: the QWheelEvent being processed
        """

        if self.leaf_numrows > self.tmodel.numrows:
            # Move the tricky scrollbar by the same amount than the hidden one.
            # Because we are moving the tricky scrollbar the dragSlider method
            # will be called
            QtCore.QCoreApplication.sendEvent(self.tricky_vscrollbar, event)
        else:
            QtGui.QTableView.wheelEvent(self, event)


    def keyPressEvent(self, event):
        """Handle basic cursor movement for key events.

        :Parameter event: the key event being processed
        """

        if self.tmodel.numrows < self.leaf_numrows:
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
        """Specialised handler for the `Home` key press event.

        See enum QAbstractitemView.CursorAction for reference.
        """

        table_size = self.tmodel.numrows
        index = self.tmodel.index(0, 0)
        # Update buffer if needed
        section = self.tmodel.rbuffer.start + 1
        if section > 1:
            self.tmodel.loadData(0, table_size)
            self.updateView()
        self.vheader.setCurrentIndex(index)
        self.scrollToTop()

        # Eventually synchronize the position of the visible scrollbar
        # the displayed data
        self.tricky_vscrollbar.setValue(0)


    def endKeyPressEvent(self):
        """Specialised handler for the `End` key press event.

        See enum QAbstractitemView.CursorAction for reference.
        """

        table_size = self.tmodel.numrows
        index = self.tmodel.index(table_size - 1, self.tmodel.numcols - 1)
        # Update buffer if needed
        section = self.tmodel.rbuffer.start + table_size
        if section < self.leaf_numrows:
            self.tmodel.loadData(self.leaf_numrows - table_size, 
                                    table_size)
            self.updateView()
        self.vheader.setCurrentIndex(index)
        self.scrollToBottom()

        # Eventually synchronize the position of the visible scrollbar
        # the displayed data
        self.tricky_vscrollbar.setValue(self.max_value)


    def upKeyPressEvent(self, event):
        """Specialised handler for the cursor up key press event.

        :Parameter event: the key event being processed
        """

        table_size = self.tmodel.numrows
        atTop = QtGui.QAbstractItemView.PositionAtTop

        # Replace the fake current cell with the valid current cell
        current_index = self.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadDatasetCurrentCell(buffer_row)
        self.scrollTo(current_index, atTop)
        buffer_start = self.tmodel.rbuffer.start

        # If we are at the first row of the buffer but not at the first
        # row of the dataset we still can go upwards so we have to read
        # the previous contiguous buffer
        if (buffer_row == 0) and (buffer_start > 0):
            self.tmodel.loadData(buffer_start - table_size, 
                                    table_size)
            self.updateView()
            # The position of the new current row
            # Beware that `buffer_start` is the first row of the OLD buffer
            if buffer_start - table_size < 0:
                row = int(buffer_start - 1)
            else:
                row = table_size - 1
            index = self.tmodel.index(row, buffer_column)
            self.setCurrentIndex(index)
            self.scrollTo(index, atTop)
        else:
            QtGui.QTableView.keyPressEvent(self, event)
            self.scrollTo(self.currentIndex(), atTop)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def pageUpKeyPressEvent(self, event):
        """Specialised handler for the `PageUp` key press event.

        :Parameter event: the key event being processed
        """

        table_size = self.tmodel.numrows
        atTop = QtGui.QAbstractItemView.PositionAtTop
        page_step = self.vscrollbar.pageStep()

        # Replace the fake current cell with the valid current cell
        current_index = self.vheader.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadDatasetCurrentCell(buffer_row)
        self.scrollTo(current_index, atTop)
        dataset_row = self.tmodel.rbuffer.start + buffer_row
        old_buffer_start = self.tmodel.rbuffer.start

        # If we are at the first page of the buffer but not at the first
        # page of the dataset we still can go upwards so we have to read
        # the previous contiguous buffer
        if (buffer_row - page_step < 0) and (self.tmodel.rbuffer.start > 0):
            self.tmodel.loadData(old_buffer_start - table_size, 
                                    table_size)
            self.updateView()
            # The position of the new current row
            row = int(dataset_row - page_step - self.tmodel.rbuffer.start)
            if row < 0:
                row = 0
            index = self.tmodel.index(row, buffer_column)
            self.vheader.setCurrentIndex(index)
            self.scrollTo(index, atTop)
        else:
            QtGui.QTableView.keyPressEvent(self, event)
            self.scrollTo(self.currentIndex(), atTop)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def downKeyPressEvent(self, event):
        """Specialised handler for the cursor down key press event.

        :Parameter event: the key event being processed
        """

        table_size = self.tmodel.numrows
        atBottom = QtGui.QAbstractItemView.PositionAtBottom

        # Replace the fake current cell with the valid current cell
        current_index = self.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadDatasetCurrentCell(buffer_row)
        self.scrollTo(current_index, atBottom)
        dataset_row = self.tmodel.rbuffer.start + buffer_row
        buffer_end = self.tmodel.rbuffer.start + table_size - 1

        # If we are at the last row of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (buffer_row == table_size - 1) and \
            (self.tmodel.rbuffer.start + table_size < self.leaf_numrows):
            self.tmodel.loadData(buffer_end + 1, table_size)
            self.updateView()
            # The position of the new current row
            # Beware that `buffer_end` is the last row of the OLD buffer
            if buffer_end + table_size > self.leaf_numrows - 1:
                row = int(dataset_row - self.tmodel.rbuffer.start + 1)
            else:
                row = 0
            index = self.tmodel.index(row, buffer_column)
            self.setCurrentIndex(index)
            self.scrollTo(index, atBottom)
        else:
            QtGui.QTableView.keyPressEvent(self, event)
            self.scrollTo(self.currentIndex(), atBottom)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()


    def pageDownKeyPressEvent(self, event):
        """Specialised handler for the `PageDown` key press event.

        :Parameter event: the key event being processed
        """

        table_size = self.tmodel.rbuffer.chunk_size
        atBottom = QtGui.QAbstractItemView.PositionAtBottom
        page_step = self.vscrollbar.pageStep()

        # Replace the fake current cell with the valid current cell
        current_index = self.vheader.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        self.loadDatasetCurrentCell(buffer_row)
        self.scrollTo(current_index, atBottom)
        dataset_row = self.tmodel.rbuffer.start + buffer_row

        # If we are at the last page of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (buffer_row + page_step > table_size - 1) and \
            (self.tmodel.rbuffer.start + table_size < self.leaf_numrows):
            self.tmodel.loadData(dataset_row + 1, table_size)
            self.updateView()
            # The position of the new current row
            row = dataset_row - self.tmodel.rbuffer.start + page_step
            if row > table_size - 1:
                row = table_size - 1
            index = self.tmodel.index(row, buffer_column)
            self.vheader.setCurrentIndex(index)
            self.scrollTo(index, atBottom)
        else:
            QtGui.QTableView.keyPressEvent(self, event)
            self.scrollTo(self.currentIndex(), atBottom)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()

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

    def currentChanged(self, current, previous):
        """Track the dataset current cell.

        This method is automatically called when the current cell changes.

        :Parameters:

        - `current`: the new current index
        - `previous`: the previous current index
        """

        if self.tmodel.numrows < self.leaf_numrows:
            row = current.row()
            column = current.column()
            self.dataset_current_cell = (self.tmodel.rbuffer.start + row, column)
        else:
            QtGui.QTableView.currentChanged(self, current, previous)


    def loadDatasetCurrentCell(self, row):
        """Load the buffer in which the valid current cell lives.

        :Parameter row: the position of the valid current cell in the model
        """

        table_size = self.tmodel.numrows
        current_section = self.dataset_current_cell[0] + 1
        if not current_section in (self.tmodel.rbuffer.start + 1, 
            self.tmodel.rbuffer.start + table_size):
            self.tmodel.loadData(current_section - row - 1, table_size)
            self.updateView()
