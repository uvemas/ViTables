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
#       $Id: vtsplash.py 1020 2008-03-28 16:41:24Z vmas $
#
########################################################################

"""
Here is defined the VTSplash class.

Classes:

* VTSplash(qt.QSplashScreen)

Methods:

* __init__(self, png)
* message(self, msg, color=qt.Qt.white)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt

class VTSplash(qt.QSplashScreen):
    """The application splash screen."""


    def __init__(self, png):
        """
        Initialize the application.

        Create a splash screen and ties it to a painter which will
        be in charge of displaying the needed messages.

        :Parameter png: the pixmap image displayed as a splash screen.
        """

        qt.QSplashScreen.__init__(self, png)
        self.painter = qt.QPainter(self.pixmap())


    def message(self, msg, color=qt.Qt.white):
        """
        Draws the message text onto the splash screen.

        Message is drawn with color color and aligns the text
        according to the flags in alignment. This is a convenience
        method. It clears the writable region before the text drawing
        and, once the drawing has been done, also repaints the splash
        screen making sure that the text will be displayed. It means
        that explicit calls to clear and repaint methods are unneeded.

        :Parameter color: the text color
        """

        # The splash pixmap has 545x350 pixels
        # Messages are drawn in a rectangle of 545x20 pixel. The top
        # left corner coordinates are (0, 330)
        self.painter.setPen(color)
        self.painter.fillRect(0, 200, 500, 17, qt.QBrush(qt.Qt.black))
        self.painter.drawText(10, 212, msg)
        self.repaint()


