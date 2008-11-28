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
#       $Id: hpScrollBar.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the HPScrollBar class.

Classes:

* HPScrollBar(qt.QScrollBar)

Methods:

* __init__(self, parent)
* eventFilter(self, w, e)
* resizeScrollBar(self)
* getSteps(self)
* getValues(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt

from vitables.vtTables.hpViewport import HPViewport

class HPScrollBar(qt.QScrollBar):
    """The scrollbar component of LeafView instances."""

    def __init__(self, parent):
        """
        Creates a customized vertical scrollbar.

        :Parameter parent:
            the parent widget (an HPTable instance) of the scrollbar
        """

        self.hpTable = parent

        # The scrollbar setup
        line, page = self.getSteps()
        minV, maxVal = self.getValues()
        v = 0
        o = qt.Qt.Vertical
        qt.QScrollBar.__init__(self, minV, maxVal, line, page, v, o, self.hpTable)

        self.installEventFilter(self)


    def eventFilter(self, w, e):
        """Filter for resize events and wheel events."""

        # Overloads the resize behaviour
        if e.type() == qt.QEvent.Resize:
            self.resizeScrollBar()
            return qt.QScrollBar.eventFilter(self, w, e)

        # Overloads the mouse wheel behaviour
        # Because the valueChanged(int) SIGNAL of the scrollbar is not
        # connected to the HPTable.syncTable slot for performance reasons
        # (see HPTable.syncTable docstring), the synchronization must be
        # done explicitely when a wheel event occurs
        elif e.type() == qt.QEvent.Wheel:
            oldValue = self.value()
            qt.QScrollBar.wheelEvent(self, e)
            newValue = self.value()
            if oldValue != newValue:
                self.hpTable.syncTable()
            return True
        # Any other event is processed here
        else:
            return qt.QScrollBar.eventFilter(self, w, e)


    def resizeScrollBar(self):
        """
        Updates the scrollbar parameters when the scrollbar resizes.

        Any resize of HPTable results in a resize of the vertical
        scrollbar of the HPViewport component, changing the range and
        page step values. However values of the embeded scrollbar remain
        constants. It forces us to syncronize values of the embeded
        components every time the container is resized.
        """

        # Get values from the embeded table
        line, page = self.getSteps()
        minV, maxVal = self.getValues()

        # Set values of the embeded scrollbar
        self.setMaxValue(maxVal)
        self.setMinValue(minV)
        self.setPageStep(page)
        self.setLineStep(line)


    def getSteps(self):
        """
        Get the line step and page step values of the scrollbar.

        :Returns:

        - `line`: the line step
        - `page`: the page step
        """

        # The scrollbar being copied
        model = self.hpTable.hpViewport.verticalScrollBar()
        line = model.lineStep()
        page = model.pageStep()
        return line, page


    def getValues(self):
        """
        Get the minimum and maximum values of the scrollbar range.

        :Returns:

        - `min`: the minimum value of the range
        - `max`: the maximum value of the range
        """

        # The scrollbar being copied
        model = self.hpTable.hpViewport.verticalScrollBar()
        min = model.minValue()
        max = model.maxValue()
        return min, max

