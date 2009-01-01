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
#       $Id: scrollBar.py 1084 2008-11-13 11:45:16Z vmas $
#
########################################################################

"""
Here is defined the ScrollBar class.

Classes:

* VScrollBar(QScrollBar)

Methods:


Functions:

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class ScrollBar(QScrollBar):
    """
    A specialised scrollbar for views of huge datasets.

    The behavior of this scrollbar is customised in a way that makes it
    suitable for dealing with huge datasets.
    """

    def __init__(self, scrollbar=None):
        """Replace a vertical scrollbar with other one.

        After replacing, the ancestor widgets of `scrollbar` looks
        exactly the same, but the visible scrollbar is not currently
        useful for navigating the data displayed in the ancestor widgets
        because it is not tied to that data in anyway.

        :Parameters:

            - `scrollbar`: the scrollbar being hidden
        """

        # Cheat the user hidding a scrollbar and displaying other one
        # that looks exactly the same
        QScrollBar.__init__(self, scrollbar.parent())
        scrollbar.setVisible(False)
        scrollbar.parent().layout().addWidget(self)
        self.setOrientation(Qt.Vertical)
    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate('VScrollBar', source, 
                                            comment).toUtf8(), 'utf_8')

