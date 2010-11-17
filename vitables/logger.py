# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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

"""Here is defined the logger module.

Classes:

* Logger(QtGui.QTextEdit)

Methods:

* __init__(self, parent=None)
* write(self, text)
* createCustomContextMenu(self, pos)
* updateEditMenu(self)
* focusInEvent(self, e)
* focusOutEvent(self, e)

Functions:

* trs(source, comment=None)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'
_context = 'Logger'

from PyQt4 import QtCore, QtGui

import vitables.utils


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


class Logger(QtGui.QTextEdit):
    """
    Logger that receives all informational application messages.

    All messages delivered by application to user are displayed in the
    logger area. This messages include the status of user requested
    operations, the result of this operations, and also error messages.
    This is possible because the class reimplement the write() method,
    so it can be used to catch both, sys.stdout an sys.stderr, just by
    redirecting them to an instance of this class.
    """

    def __init__(self, parent=None):
        """Create the Logger widget and configure it.

        :Parameter parent: the parent widget of the Logger
        """

        QtGui.QTextEdit.__init__(self, parent)
        self.setAcceptRichText(True)
        self.setReadOnly(1)
        self.setMinimumHeight(50)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setWhatsThis(trs(
            """<qt>
            <h3>The Logger</h3>
            This is the screen region where info about the currently
            selected item is displayed. It also logs the result of all
            operations requested by the user.
            <p>Also execution errors and exceptions are logged in the
            console.
            </qt>""",
            'WhatsThis help for the logger'))

        self.setStyleSheet("background-color: #ffffff")

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
            'shadow': self.frameShadow(),
            'lwidth': self.lineWidth(),
            'foreground': self.palette().color(QtGui.QPalette.Active, 
                QtGui.QPalette.WindowText)}

        # Connect signals to slots
        self.customContextMenuRequested.connect(self.createCustomContextMenu)


    def write(self, text):
        """
        The standard output and the standard error are redirected to an
        instance of Logger so we must implement a write method in order
        to display the catched messages.

        The implementation is done via QTextEdit.append method because
        this method adds the text at the end of the console so, even if
        the user clicks somewhere in the console or there is selected
        text, the printed text will not mess the console.

        :Parameter text: the text being written
        """

        current_color = self.textColor()
        if text in ['\n', '\r\n']:
            return
        if text.startswith('\nError: '):
            self.setTextColor(QtGui.QColor('red'))
        elif text.startswith('\nWarning: '):
            self.setTextColor(QtGui.QColor(243, 137, 8))
        self.append(text)
        # Warning! Append() doesn't change the cursor position
        # Because we want to reset the current color **at the end** of
        # the console in order to give the proper color to new messages
        # we must update the cursor position **before** the current
        # color is reset
        self.moveCursor(QtGui.QTextCursor.EndOfLine)
        self.setTextColor(current_color)


    def createCustomContextMenu(self, pos):
        """
        Popup the contextual logger menu.

        :Parameter pos: the local position at which the menu will popup
        """

        vtapp = vitables.utils.getVTApp()
        # Make the menu
        edit_menu = QtGui.QMenu(self)
        edit_menu.setStyleSheet("background-color: %s" % QtGui.QPalette.Window)

        self.copy_action = QtGui.QAction(
            trs("&Copy", 'Logger menu entry'), self, 
            shortcut=QtGui.QKeySequence.Copy, triggered=vtapp.makeCopy, 
            statusTip=trs('Copy selected text to clipboard', 
                'Status bar text for the logger context menu -> Copy action'))
        edit_menu.addAction(self.copy_action)

        self.clear_action = QtGui.QAction(
            trs("Cl&ear All", 'Logger menu entry'), self, 
            triggered=self.clear, 
            statusTip=trs('Empty the Logger', 
                'Status bar text for the logger context menu -> Clear action'))
        edit_menu.addAction(self.clear_action)
        edit_menu.addSeparator()

        self.select_action = QtGui.QAction(
            trs("Select &All", 'Logger menu entry'), self, 
            triggered=self.selectAll, 
            statusTip=trs('Select the whole Logger contents', 
                'Status bar text for the logger context menu -> Select All'))
        edit_menu.addAction(self.select_action)

        edit_menu.aboutToShow.connect(self.updateEditMenu)
        edit_menu.popup(self.mapToGlobal(pos))


    def updateEditMenu(self):
        """Update items availability when the menu is about to be shown."""

        # Copy is enabled when there is some selected text
        cursor = self.textCursor()
        self.copy_action.setEnabled(cursor.hasSelection())

        # Clear All and Select All are enabled when there is some text
        has_content = not self.document().isEmpty()
        self.clear_action.setEnabled(has_content)
        self.select_action.setEnabled(has_content)


    def focusInEvent(self, event):
        """Specialised handler for focus events.

        :Parameter event: the event being processed
        """

        self.setLineWidth(2)
        self.setFrameStyle(QtGui.QFrame.Panel|QtGui.QFrame.Plain)
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Active, QtGui.QPalette.WindowText, 
            QtCore.Qt.darkBlue)
        QtGui.QTextEdit.focusInEvent(self, event)


    def focusOutEvent(self, event):
        """Update the ``Node --> Copy`` action in accordance with the keyboard
        focus.

        If the logger losts keyboard focus the ``Node --> Copy`` action
        is updated.

        :Parameter event: the event being processed
        """

        self.setLineWidth(self.frame_style['lwidth'])
        self.setFrameShape(self.frame_style['shape'])
        self.setFrameShadow(self.frame_style['shadow'])
        pal = self.palette()
        pal.setColor(QtGui.QPalette.Active, QtGui.QPalette.WindowText, 
            self.frame_style['foreground'])
        QtGui.QTextEdit.focusOutEvent(self, event)

if __name__ == '__main__':
    import sys
    APP = QtGui.QApplication(sys.argv)
    LOGGER = Logger()
    LOGGER.show()
    # Redirect standard output and standard error to the Logger instance
    sys.stdout = LOGGER
    sys.stderr = LOGGER
    print 'Hola mundo!'
    print '\nError: El viatger del crepuscle'
    print '\nWarning: Adolf Piquer'
    print 'Adeu!'
    APP.exec_()
