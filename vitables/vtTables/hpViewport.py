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
#       $Id: hpViewport.py 1019 2008-03-28 12:26:43Z vmas $
#
########################################################################

"""
Here is defined the HPViewport class.

Classes:

* HPViewport(qttable.QTable)

Methods:

* __init__(self, doc, rows, cols, parent, name=None)
* columnWidthChanged(self, col)
* paintCell(self, p, row, col, cr, selected, *cg)
* getPageSize(self)
* bufferFault(self, top)
* tableFault(self, top)
* eventFilter(self, w, e)
* updateCurrentLabel(self, row, col, *args)
* getCurrentRow(self, currentLabel, inc)
* getRowLabel(self, row)
* goHome(self)
* goEnd(self)
* doGoRightLeft(self, left=False)
* doGoUp(self, step)
* doGoDown(self, step)
* contentsWheelEvent(self, e)
* nextLine(self)
* prevLine(self)
* nextPage(self)
* prevPage(self)
* doAddStep(self, step)
* doSubStep(self, step)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import numpy

import qt
import qttable

import vitables.utils
from vitables.vtWidgets.vtTableItem import VTTableItem

class HPViewport(qttable.QTable):
    """
    The viewport component of `LeafView` instances.

    This class works in combination with the `Buffer` class (i.e. it is
    implemented with a model/view architecture). It means that it 
    can be used for all kinds of data, simply by subclassing `Buffer`
    appropriately. Our data source are pytables leaves. The API to 
    access them is defined in the `NodeDoc` class and in the relevant 
    PyTables classes (mainly `Leaf` class and relatives).

    In order to improve the memory allocation the table has a fixed 
    size. So, we must overwrite the table navigation methods (arrow 
    up/down, page up/down, scrollbar line up/down, scrollbar page 
    up/down and mouse wheel rotations) in such a way that we simulate 
    the behavior of a larger table.
    """


    def __init__(self, doc, rows, cols, parent, name=None):
        """
        Create a table.

        :Parameters:

        - `doc`: 
          the document (`NodeDoc` instance) whose data we are going to show
        - `rows`: the number of rows of the table
        - `cols`: the number of columns of the table
        - `parent`:
          the parent widget of the table (an HPTable instance)
        - `name`: is None
        """

        #
        # The data source
        #
        self.doc = doc
        self.formatContent = vitables.utils.formatArrayContent
        if doc.isInstanceOf('VLArray'):
            type = doc.node.atom.type
            if type == 'object':
                self.formatContent = vitables.utils.formatObjectContent
            elif type in ('vlstring', 'vlunicode'):
                self.formatContent = vitables.utils.formatStringContent

        #
        # The table
        #
        self.hpTable = parent
        qttable.QTable.__init__(self, rows, cols, parent, name)
        self.setFocus()

        # The headers
        self.rowsHeader = self.verticalHeader()
        self.columnsHeader = self.horizontalHeader()

        # The vertical scrollbar
        self.sb = self.verticalScrollBar()

        # Install the event filter in the viewport. Every time a wheel
        # event reaches the viewport, the event will be processed by the
        # contentsWheelEvent method
        self.viewport().installEventFilter(self)

        # Table dimensions
        self.tableLength = rows
        self.numColumns = cols
        self.firstColumnWidth = self.columnWidth(0)

        # A fixed size font is a must in order to recalculate in a light
        # way the number of characters that need to be painted in the
        # paintCell method.
        table_font = qt.QFont('Monospace', 10)  # Size given in points
        table_font.setFixedPitch(True)
        table_font.setStyleHint(qt.QFont.TypeWriter)
        self.setFont(table_font)
        self.font_metrics = qt.QFontMetrics(table_font)
        self.font_info = qt.QFontInfo(table_font)
        # Characted width in pixels
        self.char_width = self.font_metrics.size(0, '1').width()

        # The array of empty cells
        self.emptyCells = {}

        # Initializes the table
        self.doc.getBuffer(0, self.doc.buffer.chunkSize)
        self.tableFault(1)
        self.setCurrentCell(0, 0)
        self.currentRowLabel = 1

        # Connect signals to slots
        self.connect(self, qt.SIGNAL('currentChanged(int, int)'),
            self.updateCurrentLabel)
        self.connect(self, qt.SIGNAL('clicked(int, int, int, const QPoint &)'),
            self.updateCurrentLabel)


    #
    # Paint cells related methods #############################################
    #


    def columnWidthChanged(self, col):
        """Repaint contents of resized columns."""


        # Initialise the array of empty cells. This way we ensure that
        # cells will be repainted by the paintCell method.
        lc = [True for i in range(0, self.numColumns)]
        for table_row in range(0, self.tableLength):
                self.emptyCells[table_row] = lc[:]

        # Repaint properly the whole table
        qttable.QTable.columnWidthChanged(self, col)


    def paintCell(self, p, row, col, cr, selected, *cg):
        """
        Paints the cell at row, col on the painter p.

        This method overloads the `QTable.paintCell` one. The point here
        is that we call setText() from inside this method, and, in 
        addition, we only process text that has not been yet displayed,
        what is a must, because converting the data being displayed to a
        string and ensuring that the string fits the available room is 
        a quite time expensive process. Doing so for the whole table 
        when a table fault is raised would slow down the navigation, and 
        the application would 'hung' for a while when doing it.

        :Parameters:

        - `p`: the painter used to paint the cell
        - `row`: the row being painted
        - `col`: the column being painted
        - `cr`: the cell rectangle in the content coordinate system
        - `selected`: if TRUE the cell is highlighted
        - `cg`: the color group which should be used to drawn the cell
        content
        """

        # Some required widths
        available_width = self.columnWidth(col)
        section_width = self.columnsHeader.sectionSize(0)

        # One column tables have their column made stretchable. They DO
        # NOT call the columnWidthChanged method when resizing occurs.
        # Moreover, I cannot manage to make the resizeEvent handler to
        # refresh them properly so I've added this block of code here.
        # Not very nice, but it works.
        if self.numColumns == 1 and available_width != self.firstColumnWidth:
            self.firstColumnWidth = available_width
            # Initialise the *whole array* of empty cells, not just the
            # cell being painted. This way the rest of cells will be
            # catched in a later if block and will be painted
            lc = [True for i in range(0, self.numColumns)]
            for table_row in range(0, self.tableLength):
                    self.emptyCells[table_row] = lc[:]

        # Give an item to the cell if needed
        if not self.item(row, col):
            self.setItem(row, col,  VTTableItem(self, ro=False))

        # Get the cell contents if needed
        if self.emptyCells[row][col]:
            self.emptyCells[row][col] = False
            l = self.rowsHeader.label(row).latin1()
            # The real row index must be an int64 in order to address
            # spaces with more than 2**32 bits
            label = numpy.array(l).astype(numpy.int64)
            content = self.doc.getCell(label - 1, col)
            text = self.formatContent(content)
    
            # The container for the final cell content
            new_text = []
            # Split the cell content in lines and get the widest line
            text_lines = text.split('\n')
            for line in text_lines:
                # Process non empty lines
                if line:
                    required_width = len(line) * self.char_width
                    # If line is wider than column then adjust line
                    if required_width > available_width:
                        invisible_chars = \
                            (required_width - available_width)/self.char_width
                        vline = line[:- invisible_chars - 2] + u'\u2026'
                        new_text.append(vline)
                    else:
                        new_text.append(line)
            # Get the new cell content by joining  the just obtained lines
            new_text = '\n'.join(new_text)
            self.setText(row, col, new_text)

        # Paint the cell
        cg = self.palette().active()
        qttable.QTable.paintCell(self, p, row, col, cr, selected, cg)



    #
    # Table fault related methods #############################################
    #


    def getPageSize(self):
        """Dinamically gets the number of visible rows of the table."""

        # The first row is placed at top edge of the viewport
        top = self.contentsY()

        # The last row is placed visibleHeight - 1 units below the first row
        firstDR = self.rowAt(top)
        lastDR = self.rowAt(top + self.visibleHeight() - 1)

        displayedRows = lastDR - firstDR + 1

        return displayedRows


    def bufferFault(self, top):
        """
        Updates the buffer contents during navigation.

        If during navigation we try to go out of the buffer (i.e. if a
        buffer fault occurs) then the buffer contents must be updated.

        A buffer fault can occur when the buffer is navigated upwards (we 
        try to go further than the top row) or downwards (we try to go
        further than the bottom row).

        :Parameter top: the label of the top row of the destination
          buffer. It is an `int64` and can address spaces with more than
          2**32 bits
        """

        # Mapping between the first and the last table rows and their
        # corresponding document rows
        firstTR = top  - 1
        lastTR = firstTR + (self.tableLength  - 1)

        #
        # Updates buffer if necessary
        #

        # If the top row of the destination table is over the buffer
        # then read a new buffer. The new buffer ends at bottom row of
       # the destination table
        if firstTR < self.doc.buffer.start:
            # last row of the buffer = last row of the table
            lastBR = lastTR
            # first row of the buffer
            # lastBR = firstBR + (self.doc.buffer.cs - 1)
            firstBR = lastBR - (self.doc.buffer.chunkSize  - 1)
            self.doc.getBuffer(firstBR, self.doc.buffer.chunkSize)

        # If the bottom row of the destination table is under the buffer
        # read a new buffer. The new buffer starts at top row of the
        # destination table
        elif lastTR >  self.doc.buffer.start + (self.doc.buffer.chunkSize - 1):
            firstBR = firstTR
            self.doc.getBuffer(firstBR, self.doc.buffer.chunkSize)

        # If the destination table is in the current buffer then a new buffer
        # is not necessary
        else:
            pass


    def tableFault(self, top):
        """
        Updates the table contents during navigation.

        If during navigation we try to go out of the table (i.e. if a
        table fault occurs) then the table contents must be updated. It
        is done filling the table with another fragment of the buffer 
        and updating the labels of sections of the vertical header of 
        the table.

        A table fault can occur when the table is navigated upwards (we 
        try to go further than the top row) or downwards (we try to go
        further than the bottom row).

        :Parameter top: the label of the top row of the destination table
        """

        # top is an int64 and can address spaces with more than 2**32 bits
        # First table row label cannot be less than 1
        if top < 1:
            top = numpy.array(1, dtype=numpy.int64)
        # Last table row label cannot be great than the number of rows
        # of the document
        elif top > self.doc.numRows() - (self.tableLength - 1):
            top = self.doc.numRows() - (self.tableLength - 1)

        #
        # Updates the buffer if it is necessary
        #
        self.bufferFault(top)

        # Initialise the array of empty cells
        lc = [True for i in range(0, self.numColumns)]
        for row in range(0, self.tableLength):
                self.emptyCells[row] = lc[:]

        #
        # Updates the labels of the vertical header of the table
        # and the table contents
        for index in range(0, self.tableLength):
            lint = index + top
            # self.rowsHeader.setLabel(index, str(lint))
            # PyQt >= 3.16 performance decreases drastically if we call
            # setLabel directly on the vertical header. The problem is fixed
            # using the alternative call QHeader.setLabel(vh, section, label)
            qt.QHeader.setLabel(self.rowsHeader, index, str(lint))

        # We must repaint labels and contents immediately or navigation methods
        # will not work properly in some situations
        self.updateHeaderStates()
        self.rowsHeader.repaint()
        self.repaintContents()

    def eventFilter(self, w, e):
        #
        # Overloads the navigation keys behaviour #############################
        #
        if e.type() == qt.QEvent.KeyPress:

            # Scroll up to the begining of the document
            if e.key() == qt.Qt.Key_Home:
                # Check for table fault
                self.goHome()
                return qttable.QTable.eventFilter(self, w, e)

            # Scroll down to the end of the document
            elif e.key() == qt.Qt.Key_End:
                # Check for table fault
                self.goEnd()
                return qttable.QTable.eventFilter(self, w, e)

            # Cursor right key pressed
            elif e.key() == qt.Qt.Key_Right:
                self.doGoRightLeft()
                return qttable.QTable.eventFilter(self, w, e)

            # Cursor left key pressed
            elif e.key() == qt.Qt.Key_Left:
                self.doGoRightLeft(True)
                return qttable.QTable.eventFilter(self, w, e)

            # Cursor up key pressed
            elif e.key() == qt.Qt.Key_Up:
                # Check for table fault
                self.doGoUp('line')
                return qttable.QTable.eventFilter(self, w, e)

            # Cursor down key pressed
            elif e.key() == qt.Qt.Key_Down:
                # Check for table fault
                self.doGoDown('line')
                return qttable.QTable.eventFilter(self, w, e)

            # Prior page key is pressed
            elif e.key() == qt.Qt.Key_Prior:
                # Check for table fault
                self.doGoUp('page')
                return qttable.QTable.eventFilter(self, w, e)

            # Next page key is pressed
            elif e.key() == qt.Qt.Key_Next:
                # Check for table fault
                self.doGoDown('page')
                return qttable.QTable.eventFilter(self, w, e)

            else:
                # Other key presses are processed in the standard way
                return qttable.QTable.eventFilter(self, w, e)

        #
        # Overloads the mouse wheel behaviour ##############################
        #
        elif e.type() == qt.QEvent.Wheel:
            # The event is never filtered, so it always reaches the viewport
            return False

        else:
            # Any other event is processed here
            return qttable.QTable.eventFilter(self, w, e)


    #
    # Current row and current label related methods ###########################
    #


    def updateCurrentLabel(self, row, col, *args):
        """
        Update the currentRowLabel variable.

        For safety, the ``currentRowLabel`` variable is setup explicitely in
        most of keyboard navigation methods (`goHome`, `goEnd`, `doGoUp`,
        `doGoDown`) after a table fault occurs. But, in absence of table
        faults, the code uses the default `QTable.eventFilter` for
        processing navigation events. In such cases this method ensures
        that ``currentRowLabel`` variable is updated.

        This method is connected to the `currentChanged(int, int)` signal
        and to the `clicked(int, int, int, QPoint)` signal.

        :Parameters:

        - `row`: the new current row
        - `col`: the new current column
        - `args`: the tuple (clicked mouse button,  mouse's position)
        """

        if (args and args[0] == qt.Qt.LeftButton) or not args:
            l = self.rowsHeader.label(row).latin1()
            label = numpy.array(l).astype(numpy.int64)
            self.currentRowLabel = label
            self.updateCell(row, col)


    def getCurrentRow(self, currentLabel, inc):
        """
        The current row after a keyboard navigation table fault.

        This method is called when keyboard navigation produces a table
        fault. It loops over the updated table, looking for the row that
        should contain the current cell and return that row (its position).

        :Parameters:

        - `currentLabel`:
          the label of the current cell before the table fault
        - `inc`: the distance that the current cell is going to be shifted

        :Returns: the position of the current row
        """

        # The label of the current row after the table fault
        newCurrentLabel = currentLabel + inc

        # Check boundaries
        if newCurrentLabel < 1:
            newCurrentLabel = 1
        elif newCurrentLabel > self.doc.numRows():
            newCurrentLabel = self.doc.numRows()

        # Loop over the whole table looking for the row that will be current
        # after the table fault
        for row in range(0, self.tableLength):
            l = self.rowsHeader.label(row).latin1()
            label = numpy.array(l).astype(numpy.int64)
            if newCurrentLabel == label:
                return row


    def getRowLabel(self, row):
        """
        The label of the given row.
        This is an accessor method used to pass info to `LeafView.slotZoomView`.

        :Returns: the label (an `int64` value) of the given row
        """
        l = self.rowsHeader.label(row).latin1()
        label = numpy.array(l).astype(numpy.int64)
        return label


    #
    # Keyboard Navigation #####################################################
    #
    # Beware these operations are current cell based
    #


    def goHome(self):
        """
        Tidy up previous to going home when the `Home` key is pressed.

        This method prepares the scenario for the posterior execution
        of `QTable.eventFilter(self, self, Qt.Key_Home)`. For safety the
        ``currentRowLabel`` variable is setup with the value it should have
        after going Home.
        """

        # Remove the focus rectangle from the current cell
        self.updateCell(self.currentRow(), self.currentColumn())

        # The label of the first row of the table
        topLabel = self.rowsHeader.label(0).latin1()
        topLabel = numpy.array(topLabel).astype(numpy.int64)

        # Boundary conditions
        outOfTable = topLabel != 1
        atHome = (self.currentRow(), self.currentRowLabel) == (0, 1)

        if not atHome and outOfTable:
            # Update the table contents
            self.tableFault(1)
            # Ensure that first row is not the current one or later
            # processing in the event filter will do nothing
            self.setCurrentCell(1, self.currentColumn())

        # The current label after going Home
        self.currentRowLabel = 1


    def goEnd(self):
        """
        Tidy up previous to going end when the `End` key is pressed.

        This method prepares the scenario for the posterior execution
        of `QTable.eventFilter(self, self, Qt.Key_End)`. For safety the
        ``currentRowLabel`` variable is setup with the value it should have
        after going End.
        """

        # Remove the focus rectangle from the current cell
        self.updateCell(self.currentRow(), self.currentColumn())

        # The label of the last row of the table
        bottomLabel = self.rowsHeader.label(self.tableLength - 1).latin1()
        bottomLabel = numpy.array(bottomLabel).astype(numpy.int64)

        # Boundary conditions
        outOfTable = bottomLabel != self.doc.numRows()
        atEnd = \
            (self.currentRow(), self.currentRowLabel) == (self.tableLength - 1,
            self.doc.numRows())

        if not atEnd and outOfTable:
            # Update properly the table contents
            self.tableFault(self.doc.numRows() - self.tableLength + 1)
            if  self.currentRow() == self.tableLength - 1:
            # Ensure that last row is not the current one or later
            # processing in the event filter will do nothing
                self.setCurrentCell(self.tableLength - 2, self.currentColumn())

        # The current label after going End
        self.currentRowLabel = self.doc.numRows()


    def doGoRightLeft(self, left=False):
        """
        Keyboard navigation right/left.

        In the event filter this method prepares the scenario for
        execution of `QTable.eventFilter(self, self, Qt.Key_Up)`. If no
        table fault occurs nothing needs to be done. If table fault
        occurs the real current row and its label need to be setup again.
        """

        curCol = self.currentColumn()
        # Remove the focus rectangle from the current cell
        self.updateCell(self.currentRow(), curCol)

        # If we are in the first column we cannot go left anymore
        if left and curCol == 0:
            return

        # If we are in the last column we cannot go right anymore
        if not left and (curCol == self.numColumns - 1):
            return

        # The label of the current row.
        currentLabel = self.rowsHeader.label(self.currentRow()).latin1()
        currentLabel = numpy.array(currentLabel).astype(numpy.int64)

        # If currentRowLabel and the current row are not synchronized
        # then display the actual current row. Later processing in the
        # event filter will update properly the current row.
        if currentLabel != self.currentRowLabel:
            self.tableFault(self.currentRowLabel - self.tableLength + 1)
            currentRow = self.getCurrentRow(self.currentRowLabel, 0)
            self.setCurrentCell(currentRow, curCol)


    def doGoUp(self, step):
        """
        Keyboard navigation upwards.

        In the event filter this method prepares the scenario for
        execution of `QTable.eventFilter(self, self, Qt.Key_Up)`. If no
        table fault occurs nothing needs to be done. If table fault
        occurs the real current row and its label need to be setup again.

        :Parameter step: the distance to scroll up. Can be 1 line or 1 page.
        """

        # Remove the focus rectangle from the current cell
        self.updateCell(self.currentRow(), self.currentColumn())

        # Get the page size
        page = self.getPageSize()

        # The distance to scroll up
        if step == 'line':
            inc = 1
        else:
            inc = page

        # The label of the current row.
        currentLabel = self.rowsHeader.label(self.currentRow()).latin1()
        currentLabel = numpy.array(currentLabel).astype(numpy.int64)

        # Boundary conditions
        atHome = (self.currentRow(), self.currentRowLabel) == (0, 1)
        outOfTable = self.currentRow() - inc < 0
        fictitiousCurrentLabel = currentLabel != self.currentRowLabel

        # If try to go out of the table (distance between the current
        # table row and the first one is less than 1 line/page) OR
        # if currentRowLabel and the current row are not synchronized
        if not atHome and (outOfTable or fictitiousCurrentLabel):
            # Display the actual current row. Later processing in the
            # event filter will update properly the current row.
            self.tableFault(self.currentRowLabel - self.tableLength + 1)
            currentRow = self.getCurrentRow(self.currentRowLabel, 0)
            self.setCurrentCell(currentRow, self.currentColumn())


    def doGoDown(self, step):
        """
        Tidy up previous to going down whith the navigation keyboard.

        In the event filter this method prepares the scenario for
        execution of `QTable.eventFilter(self, self, Qt.Key_Down)`. If no
        table fault occurs nothing needs to be done. If table fault
        occurs the real current row and its label need to be setup again.

        :Parameter step:
            the distance to scroll down. Can be 1 line or 1 page.
        """

        # Remove the focus rectangle from the current cell
        self.updateCell(self.currentRow(), self.currentColumn())

        # Get the page size
        page = self.getPageSize()

        # The distance to scroll down
        if step == 'line':
            inc = 1
        else:
            inc = page

        # The label of current row
        currentLabel = self.rowsHeader.label(self.currentRow()).latin1()
        currentLabel = numpy.array(currentLabel).astype(numpy.int64)

        # Boundary conditions
        atEnd = (self.currentRow(), self.currentRowLabel) == \
            (self.tableLength - 1, self.doc.numRows())
        outOfTable = self.currentRow() + inc > (self.tableLength - 1)
        fictitiousCurrentLabel = currentLabel != self.currentRowLabel

        # If try to go out of the table (the distance between the current table
        # row and the last one is less than 1 line/page) OR
        # If currentRowLabel and the current row are not synchronized
        if not atEnd and (outOfTable or fictitiousCurrentLabel):
            # Display the actual current row. Later processing in the
            # event filter will update properly the current row.
            self.tableFault(self.currentRowLabel)
            currentRow = self.getCurrentRow(self.currentRowLabel, 0)
            self.setCurrentCell(currentRow, self.currentColumn())


    #
    # Mouse Wheel Navigation ##################################################
    #


    def contentsWheelEvent(self, e):
        """
        Mouse wheel navigation.

        :Parameter e: the `QEvent.Wheel` event being processed
        """

        # Scroll contents as usual
        oldValue = self.sb.value()
        self.scrollBy(0, -e.delta())
        newValue = self.sb.value()

        # Check for table fault conditions
        if oldValue == newValue:
            page = self.getPageSize()

            # Scroll direction
            goUp = e.delta() > 0
            goDown = e.delta() < 0

            # If we are at the begining of the table and try to go up
            if goUp:
                # The label of the first visible row
                firstVisibleLabel = self.rowsHeader.label(0).latin1()
                firstVisibleLabel = numpy.array(firstVisibleLabel).astype(numpy.int64)

                if firstVisibleLabel > 1:
                    # Table fault
                    # The current first visible row will be the first row
                    # of the last page of the updated table
                    self.tableFault(firstVisibleLabel - self.tableLength + page)
                    l = self.rowsHeader.label(0).latin1()
                    l = numpy.array(l).astype(numpy.int64)
                    if l == 1:
                        # we have moved up less than 1 table --> The
                        # current first visible row will not be in the
                        # expected position
                        height = self.rowPos(firstVisibleLabel - 1)
                        self.setContentsPos(self.contentsX(), height)
                    else:
                        # first visible row remains the same before and after
                        # the table fault
                        self.ensureVisible(self.contentsX(),
                            self.contentsHeight(), 0, 0)

            # If we are at the end of the table and try to go down
            elif goDown:
                # The label of the last visible row
                lastVisibleLabel = self.rowsHeader.label(self.tableLength - 1).latin1()
                lastVisibleLabel = numpy.array(lastVisibleLabel).astype(numpy.int64)

                if lastVisibleLabel < self.doc.numRows():
                    # Table fault
                    # The current last visible row will be the last row
                    # of the first page of the updated table
                    self.tableFault(lastVisibleLabel + 1 - page)
                    l = self.rowsHeader.label(self.tableLength - 1).latin1()
                    l = numpy.array(l).astype(numpy.int64)
                    if l == self.doc.numRows():
                        # we have moved down less than 1 table --> The
                        # current last visible row will not be in the
                        # expected position
                        height = self.rowPos(self.tableLength + \
                            lastVisibleLabel - l)
                        self.ensureVisible(self.contentsX(), height, 0, 0)
                    else:
                        # last visible row remains the same before and after
                        # the table fault
                        self.setContentsPos(self.contentsX(), 0)


    #
    # Scrollbar Navigation ####################################################
    #
    # Beware these operations are visible screen based
    #


    def nextLine(self):
        # Line down scrollbar subcontrol pressed
        self.doAddStep(self.sb.lineStep())


    def prevLine(self):
        # Line up scrollbar subcontrol pressed
        self.doSubStep(self.sb.lineStep())


    def nextPage(self):
        # Page down scrollbar subcontrol pressed
        self.doAddStep(self.sb.pageStep())


    def prevPage(self):
        # Page up scrollbar subcontrol pressed
        self.doSubStep(self.sb.pageStep())


    def doAddStep(self, step):
        """
        Scrolls the table 1 line/page down.

        :Parameter step:
            the distance to scroll down. It is given in pixels and can
            be equivalent to 1 line or 1 page.
        """

        # The conversion factor, i.e. the number of pixels per row
        cf = self.sb.lineStep()

        # The distance to scroll down in number of rows
        inc = step/cf

        # The label of the last row of the table
        lastLabel = self.rowsHeader.label(self.tableLength - 1).latin1()
        lastLabel = numpy.array(lastLabel).astype(numpy.int64)

        # The label of the last visible row
        lvr = self.rowAt(self.contentsY() + self.visibleHeight())
        lastVisibleLabel = self.rowsHeader.label(lvr).latin1()
        lastVisibleLabel = numpy.array(lastVisibleLabel).astype(numpy.int64)

        # Boundary conditions
        outOfTable = lastVisibleLabel + inc > lastLabel
        outOfDoc = lastVisibleLabel + inc > self.doc.numRows()

        # If try to go out of the document
        if  outOfDoc:
            self.ensureVisible(self.contentsX(), self.contentsHeight(), 0, 0)
        # If try to go out of the table
        elif outOfTable:
            # Go to the next table
            self.tableFault(lastVisibleLabel)
            self.setContentsPos(self.contentsX(), 0)
        # If the scroll doesn't need to leave the current table
        else:
            # No table fault. Do a standard scroll
            self.scrollBy(0, step)


    def doSubStep(self, step):
        """
        Scrolls the table 1 line/page up.

        :Parameter step: the distance to scroll up. Can be 1 line or 1 page.
        """

        # The conversion factor from pixels to rows, i.e. the number of
        # pixels per row
        cf = self.sb.lineStep()

        # The distance to scroll up in number of rows
        inc = step/cf

        # The label of the first row
        firstLabel = self.rowsHeader.label(0).latin1()
        firstLabel = numpy.array(firstLabel).astype(numpy.int64)

        # The label of the first visible row
        fvr = self.rowAt(self.contentsY())
        firstVisibleLabel = self.rowsHeader.label(fvr).latin1()
        firstVisibleLabel = numpy.array(firstVisibleLabel).astype(numpy.int64)

        # Boundary conditions
        outOfTable = firstVisibleLabel - inc < firstLabel
        outOfDoc = firstVisibleLabel - inc < 1

        # If try to go out of the document
        if  outOfDoc:
            self.setContentsPos(self.contentsX(), 0)
        # If try to go out of the table
        elif outOfTable:
            # Go to the previous table
            self.tableFault(firstVisibleLabel - self.tableLength + 1)
            self.ensureVisible(self.contentsX(), self.contentsHeight(), 0, 0)
        # If the scroll doesn't need to leave the current table
        else:
            # No table fault. Do a standard scroll
            self.scrollBy(0, -step)

