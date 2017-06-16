#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2017 Vicent Mas. All rights reserved
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

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

import vitables.vttables.leaf_delegate as leaf_delegate
import vitables.vttables.scrollbar as scrollbar


_aiv = QtWidgets.QAbstractItemView


class LeafView(QtWidgets.QTableView):
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
        self.tmodel = tmodel  # This is a MUST
        self.leaf_numrows = leaf_numrows = self.tmodel.leaf_numrows
        self.selection_model = self.selectionModel()
        self.setSelectionMode(_aiv.SingleSelection)
        self.setSelectionBehavior(_aiv.SelectItems)

        # Setup the actual vertical scrollbar
        self.setVerticalScrollMode(_aiv.ScrollPerItem)
        self.vscrollbar = self.verticalScrollBar()

        self.setModel(tmodel)

        # For potentially huge datasets use a customised scrollbar
        if leaf_numrows > tmodel.numrows:
            self.setItemDelegate(leaf_delegate.LeafDelegate())
            self.rbuffer_fault = False
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            self.tricky_vscrollbar = scrollbar.ScrollBar(self)
            self.max_value = self.tricky_vscrollbar.setMaxValue(
                self.leaf_numrows)
            self.tricky_vscrollbar.setMinimum(0)
            self.interval_size = self.mapSlider2Leaf()

        # Setup the vertical header width
        self.vheader = QtWidgets.QHeaderView(QtCore.Qt.Vertical)
        self.setVerticalHeader(self.vheader)
        font = self.vheader.font()
        font.setBold(True)
        fmetrics = QtGui.QFontMetrics(font)
        max_width = fmetrics.width(" {0} ".format(str(leaf_numrows)))
        self.vheader.setMinimumWidth(max_width)
        self.vheader.setSectionsClickable(True)

        # Setup the headers' resize mode
        rmode = QtWidgets.QHeaderView.Stretch
        if tmodel.columnCount() == 1:
            self.horizontalHeader().setSectionResizeMode(rmode)
        if tmodel.rowCount() == 1:
            self.vheader.setSectionResizeMode(rmode)

        # Setup the text elide mode
        self.setTextElideMode(QtCore.Qt.ElideRight)

        # Connect signals to slots
        if leaf_numrows > tmodel.numrows:
            self.tricky_vscrollbar.actionTriggered.connect(
                self.navigateWithMouse)

        ## Instead of invoking updateView().
        self.setSpan(0, 0, *tmodel.get_corner_span())

    def mapSlider2Leaf(self):
        """Setup the interval size.

        Get the number of rows we move up/down on the dataset every time the
        slider's value moves up/down by 1 unit. The interval size is given by
        the formula::

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
            interval_size = round(self.leaf_numrows / self.max_value)
        return interval_size

    def syncView(self):
        """Update the tricky scrollbar value after a data navigation.

        This method every time we navigate on the table (except when we press
        the Home/End keys). Unless we are at top/bottom of the dataset the
        update is done using the first visible row as a reference.
        """

        offset = self.tmodel.start + 1
        fv_label = self.vheader.logicalIndexAt(0) + offset
        lv_label = self.vheader.logicalIndexAt(
            self.vheader.viewport().height() - 1) + offset
        if lv_label == self.leaf_numrows:
            self.tricky_vscrollbar.setValue(self.max_value)
        elif fv_label == 1:
            self.tricky_vscrollbar.setValue(0)
        else:
            value = round(fv_label / self.interval_size)
            self.tricky_vscrollbar.setValue(value)

    def updateView(self):
        """Update the view contents after a buffer fault.
        """
        tmodel = self.tmodel

        self.vheader.headerDataChanged(
            QtCore.Qt.Vertical, 0, tmodel.numrows - 1)
        top_left = tmodel.index(0, 0)
        bottom_right = tmodel.index(tmodel.numrows - 1,
                                    tmodel.numcols - 1)
        self.dataChanged(top_left, bottom_right)
        self.setSpan(0, 0, *tmodel.get_corner_span())

    def navigateWithMouse(self, slider_action):
        """Navigate the view with the mouse.

        On a regular table (with the scrollbar connected to the table view)
        this slot is called after the `action` has set the slider position
        but before the display has been updated (see documentation of the
        QAbstractSlider.actionTriggered signal in the Qt4 docs) so in this
        method we can safely do any action before that display update happens.

        In our case the slot is connected to the tricky scrollbar and its main
        functionality is to refresh model data if needed i.e, to detect buffer
        fault conditions and update the data display accordingly. If a buffer
        fault doesn't occur then the slider action is passed to the hidden
        scrollbar (which is connected to the table view) so that it can update
        the data display.

        :Parameter slider_action: the triggered slider action i.e., a member of
            the QAbstractSlider.SliderAction enum
        """

        # The QAbstractSlider.SliderAction enum values used in this method
        # QtGui.QAbstractSlider.SliderSingleStepAdd -> 1
        # QtGui.QAbstractSlider.SliderSingleStepSub -> 2
        # QtGui.QAbstractSlider.SliderPageStepAdd -> 3
        # QtGui.QAbstractSlider.SliderPageStepSub -> 4
        # QtGui.QAbstractSlider.SliderMove -> 7
        actions = {
            1: self.addSingleStep,
            2: self.subSingleStep,
            3: self.addPageStep,
            4: self.subPageStep,
            7: self.dragSlider
        }
        if slider_action not in actions.keys():
            return
        # Navigate the data dealing with buffer faults
        actions[slider_action]()

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()

    def mouseNavInfo(self, direction):
        """Gives information about model, vertical header and viewport.

        This is a helper method used by methods that browse the data via mouse.

        :Parameter direction: the data browsing direction (upwards/downwards)
        """

        model = self.tmodel
        vh = self.vheader

        # About the table
        table_rows = model.numrows
        buffer_start = model.start

        # The viewport BEFORE navigating the data
        if (direction == 'u'):
            row = vh.visualIndexAt(0)
        elif (direction == 'd'):
            row = vh.visualIndexAt(self.viewport().height())
        page_step = self.vscrollbar.pageStep()

        return (model, vh, table_rows, buffer_start, row, page_step)

    def addSingleStep(self):
        """Setup data for moving towards the last section line by line.
        """

        model, vh, table_rows, buffer_start, last_vp_row, page_step = \
            self.mouseNavInfo('d')
        # If we are at the last row of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (last_vp_row + 1 == table_rows) and \
                (buffer_start + table_rows < self.leaf_numrows):
            # Buffer fault. The new buffer starts just after the current
            # first row of the viewport.
            new_start = buffer_start + last_vp_row - page_step + 1
            model.loadData(new_start, table_rows)
            self.updateView()
            self.scrollTo(
                model.index(new_start - model.start, 0),
                _aiv.PositionAtTop)
        else:
            self.vscrollbar.triggerAction(1)

    def addPageStep(self):
        """Setup data for moving towards the last section page by page.
        """

        model, vh, table_rows, buffer_start, last_vp_row, page_step = \
            self.mouseNavInfo('d')
        # If we are at the last page of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (last_vp_row + page_step + 1 > table_rows) and \
                (buffer_start + table_rows < self.leaf_numrows):
            # Buffer fault. The new buffer starts at the current last
            # row of the viewport.
            new_start = buffer_start + last_vp_row
            model.loadData(new_start, table_rows)
            self.updateView()
            self.scrollTo(
                model.index(new_start - model.start, 0),
                _aiv.PositionAtTop)
        else:
            self.vscrollbar.triggerAction(3)

    def subSingleStep(self):
        """Setup data for moving towards the first section line by line.
        """

        model, vh, table_rows, buffer_start, first_vp_row, page_step = \
            self.mouseNavInfo('u')
        # If we are at the first row of the buffer but not at the first
        # row of the dataset we still can go upwards so we have to
        # read the previous contiguous buffer
        if (first_vp_row == 0) and (buffer_start > 0):
            # Buffer fault. The new buffer ends just before the current
            # last row of the viewport.
            model.loadData(
                buffer_start + page_step - table_rows, table_rows)
            self.scrollTo(
                model.index(buffer_start + page_step - model.start - 1, 0),
                _aiv.PositionAtBottom)
            self.updateView()
        else:
            self.vscrollbar.triggerAction(2)

    def subPageStep(self):
        """Setup data for moving towards the first section page by page.
        """

        model, vh, table_rows, buffer_start, first_vp_row, page_step = \
            self.mouseNavInfo('u')
        # If we are at the first page of the buffer but not at the first
        # row of the dataset we still can go upwards so we have to
        # read the previous contiguous buffer
        if (first_vp_row < page_step + 1) and (buffer_start > 0):
            # Buffer fault. The new buffer ends just at the current
            # first row of the viewport.
            model.loadData(
                buffer_start + first_vp_row - table_rows + 1,
                table_rows)
            self.updateView()
            self.scrollTo(
                model.index(
                    buffer_start + first_vp_row - model.start, 0),
                _aiv.PositionAtBottom)
        else:
            self.vscrollbar.triggerAction(4)

    def dragSlider(self):
        """Move the slider by dragging it.

        When navigating large datasets we must beware that the number of
        rows of the dataset (int64) is greater than the number of
        values in the range of values (int32) of the scrollbar. It means
        that there are rows that cannot be reached with the scrollbar.

        Note:: QScrollBar.sliderPosition and QScrollBar.value not always
        return the same value. When we reach the top of the dataset:

        - wheeling: value() returns 0, sliderPosition() returns a
            negative number
        - dragging: value() returns a number greater than 0, sliderPosition()
            returns 0
        """

        model = self.tmodel
        table_rows = model.numrows
        value = self.tricky_vscrollbar.sliderPosition()
        if value < 0:
            value = 0
            row = 0
        elif value >= self.max_value:
            value = self.max_value
            row = self.leaf_numrows - 1
        else:
            row = self.interval_size * value

        # top buffer fault condition
        if row < model.start:
            self.topBF(value, row)
        # bottom buffer fault condition
        elif (row >= model.start + table_rows):
            self.bottomBF(value, row)
        # We are at top of the dataset
        elif value == self.tricky_vscrollbar.minimum():
            self.vscrollbar.triggerAction(
                QtWidgets.QAbstractSlider.SliderToMinimum)
        # We are at bottom of the dataset
        elif value == self.tricky_vscrollbar.maximum():
            self.vscrollbar.triggerAction(
                QtWidgets.QAbstractSlider.SliderToMaximum)
        # we are somewhere in the middle of the dataset
        else:
            self.scrollTo(
                model.index(row - model.start, 0),
                _aiv.PositionAtTop)

    def topBF(self, value, row):
        """Going out of buffer when browsing upwards.

        Buffer fault condition: row < model.start

        :Parameters:

            - `value`: the current value of the tricky scrollbar
            - `row`: the estimated dataset row mapped to that value
        """

        table_rows = self.tmodel.numrows
        if value == self.tricky_vscrollbar.minimum():
            start = 0
            position = 0
            hint = _aiv.PositionAtTop
            self.vscrollbar.triggerAction(
                QtWidgets.QAbstractSlider.SliderToMinimum)
        else:
            start = row - table_rows
            position = table_rows - 1
            hint = _aiv.PositionAtBottom

        self.tmodel.loadData(start, table_rows)
        self.updateView()
        self.scrollTo(self.tmodel.index(position, 0), hint)

    def bottomBF(self, value, row):
        """Going out of buffer when browsing downwards.

        Buffer fault condition: row > self.tmodel.start + table_rows - 1

        :Parameters:

            - `value`: the current value of the tricky scrollbar
            - `row`: the estimated dataset row mapped to that value
        """

        table_rows = self.tmodel.numrows
        if value == self.tricky_vscrollbar.maximum():
            row = self.leaf_numrows - 1
            start = self.leaf_numrows - table_rows
            position = table_rows - 1
            hint = _aiv.PositionAtBottom
            self.vscrollbar.triggerAction(
                QtWidgets.QAbstractSlider.SliderToMinimum)
        else:
            start = row
            position = 0
            hint = _aiv.PositionAtTop

        self.tmodel.loadData(start, table_rows)
        self.updateView()
        self.scrollTo(self.tmodel.index(position, 0), hint)

    def wheelEvent(self, event):
        """Specialized handler for the wheel events received by the *viewport*.

        :Parameter event: the QWheelEvent being processed
        """

        if self.leaf_numrows > self.tmodel.numrows:
            height = self.vheader.sectionSize(0)
            # The distance the wheel is rotated in eights of a degree.
            # For example: 120/8 = 15 so if delta is 120 then the wheel
            # has been rotated by 15 degrees. It *seems* that every eight of
            # degree corresponds to a distance of 1 pixel.
            delta = event.angleDelta().y()
            self.wheel_step = round(abs(delta) / height) - 1
            if delta < 0:
                self.wheelDown(event)
            else:
                self.wheelUp(event)
            self.syncView()
            # Filter the event so it will not be passed to the parent widget
            event.accept()
        else:
            QtWidgets.QTableView.wheelEvent(self, event)

    def wheelDown(self, event):
        """Setup data for wheeling with the mouse towards the last section.
        """

        model, vh, table_rows, buffer_start, last_vp_row, page_step = \
            self.mouseNavInfo('d')
        vp_rows = last_vp_row - vh.visualIndexAt(0)
        # If we are at the last page of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (last_vp_row + self.wheel_step + 1 > table_rows) and \
                (buffer_start + table_rows < self.leaf_numrows):
            # Buffer fault. The new buffer and the old one overlap to ensure
            # that no jumps occur.
            new_start = \
                buffer_start + last_vp_row + self.wheel_step - page_step
            model.loadData(new_start, table_rows)
            self.updateView()
            self.scrollTo(model.index(new_start - model.start, 0),
                          _aiv.PositionAtTop)
        else:
            QtCore.QCoreApplication.sendEvent(self.vscrollbar, event)

    def wheelUp(self, event):
        """Setup data for wheeling with the mouse towards the first section.
        """

        model, vh, table_rows, buffer_start, first_vp_row, page_step = \
            self.mouseNavInfo('u')
        vp_rows = vh.visualIndexAt(self.viewport().height()) - first_vp_row
        # If we are at the first page of the buffer but not at the first
        # row of the dataset we still can go upwards so we have to
        # read the previous contiguous buffer
        if (first_vp_row < page_step + 1) and (buffer_start > 0):
            # Buffer fault. The new buffer and the old one overlap to ensure
            # that no jumps occur.
            new_start = buffer_start + first_vp_row + page_step - \
                self.wheel_step - table_rows + 1
            model.loadData(new_start, table_rows)
            self.updateView()
            self.scrollTo(
                model.index(
                    new_start + table_rows - model.start - 1, 0),
                _aiv.PositionAtBottom)
        else:
            QtCore.QCoreApplication.sendEvent(self.vscrollbar, event)

    def keyPressEvent(self, event):
        """Handle basic cursor movement for key events.

        :Parameter event: the key event being processed
        """

        if self.tmodel.numrows < self.leaf_numrows:
            key = event.key()
            if key == QtCore.Qt.Key_Home:
                event.accept()
                self.homeKeyPressEvent()
            elif key == QtCore.Qt.Key_End:
                event.accept()
                self.endKeyPressEvent()
            elif key == QtCore.Qt.Key_Up:
                event.accept()
                self.upKeyPressEvent(event)
            elif key == QtCore.Qt.Key_Down:
                event.accept()
                self.downKeyPressEvent(event)
            elif key == QtCore.Qt.Key_PageUp:
                event.accept()
                self.pageUpKeyPressEvent(event)
            elif key == QtCore.Qt.Key_PageDown:
                event.accept()
                self.pageDownKeyPressEvent(event)
            else:
                QtWidgets.QTableView.keyPressEvent(self, event)
        else:
            QtWidgets.QTableView.keyPressEvent(self, event)

    def homeKeyPressEvent(self):
        """Specialised handler for the `Home` key press event.

        See enum QAbstractitemView.CursorAction for reference.
        """

        model = self.tmodel
        table_rows = model.numrows
        index = model.index(0, 0)
        # Update buffer if needed
        if model.start > 0:
            model.loadData(0, table_rows)
            self.updateView()
        self.setCurrentIndex(index)
        self.scrollToTop()

        # Eventually synchronize the position of the visible scrollbar
        # the displayed data
        self.tricky_vscrollbar.setValue(0)

    def endKeyPressEvent(self):
        """Specialised handler for the `End` key press event.

        See enum QAbstractitemView.CursorAction for reference.
        """

        model = self.tmodel
        table_rows = model.numrows
        index = model.index(table_rows - 1, model.numcols - 1)
        # Update buffer if needed
        last_row = model.start + table_rows
        if last_row < self.leaf_numrows:
            self.tmodel.loadData(self.leaf_numrows - table_rows,
                                 table_rows)
            self.updateView()
        self.setCurrentIndex(index)
        self.scrollToBottom()

        # Eventually synchronize the position of the visible scrollbar
        # the displayed data
        self.tricky_vscrollbar.setValue(self.max_value)

    def keyboardNavInfo(self):
        """Gives information about model, and current cell.

        This is a helper method used by methods that browse the data via
        keyboard.

        :Parameter direction: the data browsing direction (upwards/downwards)
        """

        model = self.tmodel
        # Load the buffer where the valid current cell lives
        self.validCurrentCellBuffer()

        # About the table
        table_rows = model.numrows
        buffer_start = model.start

        page_step = self.vscrollbar.pageStep()

        # About the current cell
        current_index = self.currentIndex()
        buffer_row = current_index.row()
        buffer_column = current_index.column()
        dataset_row = buffer_start + buffer_row

        return (model, table_rows, buffer_start, page_step, current_index,
                buffer_row, buffer_column, dataset_row)

    def upKeyPressEvent(self, event):
        """Specialised handler for the cursor up key press event.

        :Parameter event: the key event being processed
        """

        (model, table_rows, buffer_start, page_step, current_index,
            buffer_row, buffer_column, dataset_row) = self.keyboardNavInfo()

        # If we are at the first row of the buffer but not at the first
        # row of the dataset we still can go upwards so we have to read
        # the previous contiguous buffer
        if (buffer_row == 0) and (buffer_start > 0):
            model.loadData(dataset_row - table_rows + page_step, table_rows)
            self.updateView()
            # The position of the new current row
            row = dataset_row - model.start - 1
            if row < 0:
                row = 0
            index = model.index(row, buffer_column)
            self.setCurrentIndex(index)
            self.scrollTo(index,
                          _aiv.PositionAtTop)
        else:
            QtWidgets.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()

    def pageUpKeyPressEvent(self, event):
        """Specialised handler for the `PageUp` key press event.

        :Parameter event: the key event being processed
        """

        (model, table_rows, buffer_start, page_step, current_index,
            buffer_row, buffer_column, dataset_row) = self.keyboardNavInfo()

        # If we are at the first page of the buffer but not at the first
        # page of the dataset we still can go upwards so we have to read
        # the previous contiguous buffer
        if (buffer_row - page_step < 0) and (buffer_start > 0):
            model.loadData(dataset_row - table_rows, table_rows)
            self.updateView()
            # The position of the new current row
            row = dataset_row - model.start - page_step - 1
            if row < 0:
                row = 0
            index = model.index(row, buffer_column)
            self.setCurrentIndex(index)
            self.scrollTo(index,
                          _aiv.PositionAtTop)
        else:
            QtWidgets.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()

    def downKeyPressEvent(self, event):
        """Specialised handler for the cursor down key press event.

        :Parameter event: the key event being processed
        """

        (model, table_rows, buffer_start, page_step, current_index,
            buffer_row, buffer_column, dataset_row) = self.keyboardNavInfo()

        # If we are at the last row of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (buffer_row == table_rows - 1) and \
                (buffer_start + table_rows < self.leaf_numrows):
            model.loadData(dataset_row - page_step + 1, table_rows)
            self.updateView()
            # The position of the new current row
            row = dataset_row - model.start + 1
            if row > table_rows - 1:
                row = table_rows - 1
            index = model.index(row, buffer_column)
            self.setCurrentIndex(index)
            self.scrollTo(index,
                          _aiv.PositionAtBottom)
        else:
            QtWidgets.QTableView.keyPressEvent(self, event)

        # Eventually synchronize the position of the visible scrollbar
        # with the displayed data using the first visible cell as
        # reference
        self.syncView()

    def pageDownKeyPressEvent(self, event):
        """Specialised handler for the `PageDown` key press event.

        :Parameter event: the key event being processed
        """

        (model, table_rows, buffer_start, page_step, current_index,
            buffer_row, buffer_column, dataset_row) = self.keyboardNavInfo()

        # If we are at the last page of the buffer but not at the last
        # row of the dataset we still can go downwards so we have to
        # read the next contiguous buffer
        if (buffer_row + page_step > table_rows - 1) and \
                (buffer_start + table_rows < self.leaf_numrows):
            model.loadData(dataset_row + 1, table_rows)
            self.updateView()
            # The position of the new current row
            row = dataset_row - model.start + page_step + 1
            if row > table_rows - 1:
                row = table_rows - 1
            index = model.index(row, buffer_column)
            self.setCurrentIndex(index)
            self.scrollTo(index,
                          _aiv.PositionAtBottom)
        else:
            QtWidgets.QTableView.keyPressEvent(self, event)

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
    # cell *fake current cell*. This would be a bug.

    def currentChanged(self, current, previous):
        """Track the dataset current cell.

        This SLOT is automatically called when the current cell changes.

        :Parameters:

        - `current`: the new current index
        - `previous`: the previous current index
        """

        QtWidgets.QTableView.currentChanged(self, current, previous)
        if self.tmodel.numrows < self.leaf_numrows:
            self.valid_current_buffer = self.tmodel.start

    # This method has been renamed from loadDatasetCurrentCell to
    # validCurrentCellBuffer. The method has been debugged too
    def validCurrentCellBuffer(self):
        """Load the buffer in which the valid current cell lives.
        """

        table_rows = self.tmodel.numrows
        valid_current = self.currentIndex().row() + self.valid_current_buffer
        if not (self.tmodel.start <=
                valid_current <=
                self.tmodel.start + table_rows - 1):
            self.tmodel.loadData(self.valid_current_buffer, table_rows)
            self.updateView()

    def selectionChanged(self, selected, deselected):
        """Track the dataset selected cells.

        This method is automatically called when the selected range changes.

        :Parameters:

        - `selected`: the new selection
        - `deselected`: the previous selection (maybe empty)
        """

        model = self.tmodel
        if model.numrows < self.leaf_numrows:
            # Get the selected indexes from the QItemSelection object
            selection = selected.indexes()
            if len(selection):
                model.selected_cell = {
                    'index': selection[0],
                    'buffer_start': model.start,
                }
        else:
            QtWidgets.QTableView.selectionChanged(self, selected, deselected)
