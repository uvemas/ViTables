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
This minimal module makes a QScrollBar for browsing huge datasets.

The use of this scrollbar is very tricky. It will be painted over the scrollbar
of views bound to huge datasets so the view will look as usual but will have 2
scrollbars. The hidden scrollbar is not useful for browsing huge datasets (it
is tightly bound to the dimensions (number of rows) of the view widget. But the
visible scrollbar is independent of the dimensions of the view widget and can
be used for customising the view in a way that makes it useful for browsing
datasets with a larger number of rows than that provided by the view widget.
"""

__docformat__ = 'restructuredtext'

from qtpy.QtCore import Qt
from qtpy.QtCore import QEvent
from qtpy.QtWidgets import QScrollBar


class ScrollBar(QScrollBar):
    """
    A specialised scrollbar for views of huge datasets.

    :Parameter scrollbar: the scrollbar being hidden
    """

    def __init__(self, view):
        """Replace a vertical scrollbar with other one.

        After replacing, the ancestor widgets of `scrollbar` looks
        exactly the same, but the visible scrollbar is not currently
        useful for navigating the data displayed in the ancestor widgets
        because it is not tied to that data in anyway.
        """

        self.view = view
        # Cheat the user hidding a scrollbar and displaying other one
        # that looks exactly the same
        parent = view.vscrollbar.parent()
        super(ScrollBar, self).__init__(parent)
        view.vscrollbar.setVisible(False)
        parent.layout().addWidget(self)
        self.setOrientation(Qt.Vertical)
        self.setObjectName('tricky_vscrollbar')

    def event(self, e):
        """Filter wheel events and send them to the table viewport. """
        if (e.type() == QEvent.Wheel):
            self.view.wheelEvent(e)
            return True
        return QScrollBar.event(self, e)

    def setMaxValue(self, max_value):
        """Ensure range of scrollbar is a signed 32bit integer."""
        max_value = min(2 ** 31 - 1, max_value)
        self.setMaximum(max_value)

        return max_value
