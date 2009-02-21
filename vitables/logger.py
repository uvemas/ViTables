#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
#       $Id: logger.py 1026 2008-03-19 19:51:07Z vmas $
#
########################################################################

"""Here is defined the logger module.

Classes:

* Logger(QTextEdit)

Methods:

* __init__(self, parent=None)
* __tr(self, source, comment=None)
* write(self, text)
* createCustomContextMenu(self, pos)
* updateEditMenu(self)
* disableCopyNodeAction(self)
* enableCopyNodeAction(self)
* focusInEvent(self, e)
* focusOutEvent(self, e)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Logger(QTextEdit):
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

        QTextEdit.__init__(self, parent)
        self.setAcceptRichText(True)
        self.setReadOnly(1)
        self.setMinimumHeight(50)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setWhatsThis(self.__tr(
            """<qt>
            <h3>The Logger</h3>
            This is the screen region where info about the currently
            selected item is displayed. It also logs the result of all
            operations requested by the user.
            <p>Also execution errors and exceptions are logged in the
            console.
            </qt>""",
            'WhatsThis help for the logger'))

        self.setStyleSheet("""background-color: #ffffff""")

        # The frame especification
        self.frame_style = {'shape': self.frameShape(),
            'shadow': self.frameShadow(),
            'lwidth': self.lineWidth(),
            'foreground': self.palette().color(QPalette.Active, 
                QPalette.WindowText)}

        # Connect signals to slots
        self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"),
            self.createCustomContextMenu)
    def __tr(self, source, comment=None):
        """Translate method."""
        return unicode(qApp.translate('Logger', source, comment))


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
            self.setTextColor(QColor('red'))
        elif text.startswith('\nWarning: '):
            self.setTextColor(QColor(243, 137, 8))
        self.append(text)
        # Warning! Append() doesn't change the cursor position
        # Because we want to reset the current color **at the end** of
        # the console in order to give the proper color to new messages
        # we must update the cursor position **before** the current
        # color is reset
        self.moveCursor(QTextCursor.EndOfLine)
        self.setTextColor(current_color)

    def createCustomContextMenu(self, pos):
        """
        Popup the contextual logger menu.

        :Parameter pos: the local position at which the menu will popup
        """

        # Make the menu
        edit_menu = QMenu(self)
        self.copy_action = edit_menu.addAction(
            self.__tr("&Copy", 'Logger menu entry'),
            self, SLOT('copy()'),
            QKeySequence('CTRL+C'))
        self.clear_action = edit_menu.addAction(
            self.__tr("Cl&ear All", 'Logger menu entry'),
            self, SLOT('clear()'))
        edit_menu.addSeparator()
        self.select_action = edit_menu.addAction(
            self.__tr("Select &All", 'Logger menu entry'),
            self, SLOT('selectAll()'))

        self.connect(edit_menu, SIGNAL('aboutToShow()'),
            self.updateEditMenu)
        self.connect(edit_menu, SIGNAL('aboutToShow()'),
            self.disableCopyNodeAction)
        self.connect(edit_menu, SIGNAL('aboutToHide()'),
            self.updateCopyNodeAction)

        edit_menu.popup(self.mapToGlobal(pos))
    def updateEditMenu(self):
        """Update items availability when the menu is about to be shown."""

        # Copy is enabled when there is some selected text
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.copy_action.setEnabled(True)
        else:
            self.copy_action.setEnabled(False)

        # Clear All and Select All are enabled when there is some text
        document = self.document()
        if document.isEmpty():
            self.clear_action.setEnabled(False)
            self.select_action.setEnabled(False)
        else:
            self.clear_action.setEnabled(True)
            self.select_action.setEnabled(True)


    def disableCopyNodeAction(self):
        """
        Disable the status of the Copy node action.

        This method is called whenever the logger gets keyboard
        focus or its contextual menu is shown.
        """
        self.emit(SIGNAL('disableCopyNodeAction()'), ())

    def updateCopyNodeAction(self):
        """
        Update the status of the Copy node action.

        This method is called whenever the logger losts keyboard
        focus or its contextual menu is hiden.
        """
        self.emit(SIGNAL('updateCopyNodeAction()'), ())

    def focusInEvent(self, event):
        """Specialised handler for focus events.

        :Parameter event: the event being processed
        """

        self.disableCopyNodeAction()
        self.setLineWidth(2)
        self.setFrameStyle(QFrame.Panel|QFrame.Plain)
        pal = self.palette()
        pal.setColor(QPalette.Active, QPalette.WindowText, Qt.darkBlue)
        QTextEdit.focusInEvent(self, event)


    def focusOutEvent(self, event):
        """Update the ``Node --> Copy`` action in accordance with the keyboard
        focus.

        If the logger losts keyboard focus the ``Node --> Copy`` action
        is updated.

        :Parameter event: the event being processed
        """

        self.updateCopyNodeAction()
        self.setLineWidth(self.frame_style['lwidth'])
        self.setFrameShape(self.frame_style['shape'])
        self.setFrameShadow(self.frame_style['shadow'])
        pal = self.palette()
        pal.setColor(QPalette.Active, QPalette.WindowText, 
            self.frame_style['foreground'])
        QTextEdit.focusOutEvent(self, event)

if __name__ == '__main__':
    import sys
    APP = QApplication(sys.argv)
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
