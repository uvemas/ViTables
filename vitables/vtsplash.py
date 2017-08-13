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
Here is defined the VTSplash class. It displays the splash screen during the
``ViTables`` startup and shows the advance of the startup sequence.
"""

import time

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets


__docformat__ = 'restructuredtext'


class VTSplash(QtWidgets.QSplashScreen):
    """
    The application splash screen.

    :Parameter png: the pixmap image displayed as a splash screen.
    """

    def __init__(self, png):
        """
        Initialize the application.

        Create a splash screen and ties it to a painter which will
        be in charge of displaying the needed messages.
        """

        super(VTSplash, self).__init__(png)
        self.msg = ''

    def drawContents(self, painter):
        """Draw the contents of the splash screen using the given painter.

        This is an overloaded method. It draws contents with the origin
        translated by a certain offset.

        :Parameter painter: the painter used to draw the splash screen
        """

        painter.setPen(QtGui.QColor(QtCore.Qt.white))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 215, self.msg)

    def drawMessage(self, msg):
        """
        Draw the message text onto the splash screen.

        :Parameter msg: the message to be displayed
        """

        QtWidgets.qApp.processEvents()
        self.msg = msg
        self.showMessage(self.msg)
        time.sleep(0.500)
        self.clearMessage()
