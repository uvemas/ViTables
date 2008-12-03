# -*- coding: utf-8 -*-
#!/usr/bin/env python


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
#       $Id: vtsplash.py 1063 2008-09-24 17:30:22Z vmas $
#
########################################################################

"""
Here is defined the VTSplash class.

Classes:

* VTSplash(QtGui.QSplashScreen)

Methods:

* __init__(self, png)
* drawContents(self, painter)
* drawMessage(self, msg)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import time

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

class VTSplash(QtGui.QSplashScreen):
    """The application splash screen."""

    def __init__(self, png):
        """
        Initialize the application.

        Create a splash screen and ties it to a painter which will
        be in charge of displaying the needed messages.

        :Parameter png: the pixmap image displayed as a splash screen.
        """

        QtGui.QSplashScreen.__init__(self, png)


    def drawContents(self, painter):
        """Draw the contents of the splash screen using a given painter.

        This is an overloaded method. It draws contents with the origin
        translated by a certain offset.

        :Parameter painter: the painter used to draw the splash screen
        """

        painter.setPen(QtGui.QColor(QtCore.Qt.white))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, 213, self.msg)


    def drawMessage(self, msg):
        """
        Draws the message text onto the splash screen.

        :Parameter msg: the message to be displayed
        """

        QtGui.qApp.processEvents()
        self.msg = msg
        self.showMessage(self.msg)
        time.sleep(0.500)
        self.clearMessage()


if __name__ == '__main__':
    import sys
    import time
    APP = QtGui.QApplication(sys.argv)
    LOGO = QtGui.QPixmap("""/home/vmas/repositoris.nobackup/"""
        """vitables/icons/vitables_logo.png""")
    SPLASH = VTSplash(LOGO)
    SPLASH.show()
    # Check that messages are not overwritten:
    # write a message, wait a little bit, write another message
    SPLASH.drawMessage('hola, que tal estas?')
    QtGui.qApp.processEvents()
    time.sleep(3)
    SPLASH.drawMessage('hasta luego, lucas!')
#    qtGui.qApp.processEvents()
    TIMER = QtCore.QTimer()
    TIMER.connect(TIMER, QtCore.SIGNAL('timeout()'), QtGui.qApp.quit)
    TIMER.setSingleShot(True)
    TIMER.start(3000)
    APP.exec_()

