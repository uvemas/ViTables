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
#       $Id: preferences.py 1083 2008-11-04 16:41:02Z vmas $
#
########################################################################

"""
Here is defined the Preferences class.

Classes:

* Preferences(QtCore.QObject)

Methods:

* __init__(self, vtapp)
* __tr(self, source, comment=None)
* setPreferences(self, preferences)
* slotApplyButton(self)
* slotButtonClicked(self, button)
* slotCancelButton(self)
* slotOKButton(self)
* slotResetButton(self)
* slotSetLoggerBackground(self)
* slotSetLoggerFont(self)
* slotSetLoggerForeground(self)
* slotSetStartupDir(self, button_id)
* slotSetStartupSession(self, cb_on)
* slotSetStyle(self, style_name)
* slotSetWorkspaceBackground(self)

Misc variables:

* __docformat__

"""

__docformat__ = 'restructuredtext'

import PyQt4.QtCore as QtCore
import PyQt4.QtGui as QtGui

from vitables.preferences.preferencesGUI import PreferencesGUI

class Preferences(QtCore.QObject):
    """
    Gives functionality to the `Preferences` dialog.
    """

    def __init__(self, vtapp):
        """
        Initialize the preferences dialog.

        * initializes the GUI appearance according to current preferences
        * connects dialog widgets to slots that provide them functionality

        :Parameters:

        - `vtapp`: an instance of VTApp
        """

        QtCore.QObject.__init__(self)

        # Radio button names are not usable, we need the numerical IDs
        self.button2id = {QtCore.QString('home'): 1, QtCore.QString('last'): 2}

        self.vtapp = vtapp
        self.gui = PreferencesGUI()

        # The current preferences of the application
        self.initial_prefs = {}
        style_sheet = vtapp.logger.styleSheet()
        paper = style_sheet[-7:]
        self.initial_prefs['Logger/paper'] = QtGui.QColor(paper)
        self.initial_prefs['Logger/text'] = vtapp.logger.textColor()
        self.initial_prefs['Logger/font'] = vtapp.logger.font()
        self.initial_prefs['Workspace/background'] = \
                                        vtapp.workspace.background().color()
        self.initial_prefs['Look/currentStyle'] = vtapp.current_style
        self.initial_prefs['Startup/startupWorkingDirectory'] = \
                                                vtapp.startup_working_directory
        self.initial_prefs['Startup/restoreLastSession'] = \
                                                    vtapp.restore_last_session

        # The dictionary used to update the preferences
        self.new_prefs = {}

        self.setPreferences(self.initial_prefs)

        # Connect SIGNALS to SLOTS
        # Apply, OK, Reset and Cancel buttons
        self.connect(self.gui.buttons_box, 
            QtCore.SIGNAL('clicked(QAbstractButton *)'),
            self.slotButtonClicked)
        # Startup groupbox
        self.connect(self.gui.hiden_bg, QtCore.SIGNAL('buttonClicked(int)'),
            self.slotSetStartupDir)
        self.connect(self.gui.restore_cb, QtCore.SIGNAL('toggled(bool)'),
            self.slotSetStartupSession)
        # Logger groupbox
        self.connect(self.gui.font_pb, QtCore.SIGNAL('clicked()'),
            self.slotSetLoggerFont)
        self.connect(self.gui.foreground_pb, QtCore.SIGNAL('clicked()'),
            self.slotSetLoggerForeground)
        self.connect(self.gui.background_pb, QtCore.SIGNAL('clicked()'),
            self.slotSetLoggerBackground)
        # Workspace groupbox
        self.connect(self.gui.workspace_pb, QtCore.SIGNAL('clicked()'),
            self.slotSetWorkspaceBackground)
        # Style groupbox
        self.connect(self.gui.styles_cb,
            QtCore.SIGNAL('activated(QString)'), self.slotSetStyle)


    def __tr(self, source, comment=None):
        """Translate method."""
        return str(QtGui.qApp.translate('Preferences', source, comment))


    def setPreferences(self, preferences):
        """
        Applies a given set of preferences to the Preferences dialog.

        :Parameter preferences:
            a dictionary with current configuration settings
        """

        rb_id = self.button2id[\
            preferences['Startup/startupWorkingDirectory']]
        self.gui.hiden_bg.button(rb_id).setChecked(True)

        self.gui.restore_cb.setChecked(\
            preferences['Startup/restoreLastSession'])

        self.gui.sample_te.selectAll()
        self.gui.sample_te.setTextColor(preferences['Logger/text'])
        self.gui.sample_te.moveCursor(QtGui.QTextCursor.End)  # Unselect text
        self.gui.sample_te.setStyleSheet("""background-color: %s""" % 
                                        preferences['Logger/paper'].name())
        self.gui.sample_te.setFont(preferences['Logger/font'])

        self.gui.workspace_label.setStyleSheet('background-color: %s' % 
            preferences['Workspace/background'].name())

        index = self.gui.styles_cb.findText(\
            preferences['Look/currentStyle'])
        self.gui.styles_cb.setCurrentIndex(index)


    def slotButtonClicked(self, button):
        """Manages dialog button cliksin the Preferences dialog.

        Whenever one of the Apply, Reset, Cancel or OK buttons is
        clicked in the Preferences dialog this slot is called.

        :Parameter button: the clicked button.
        """

        if button == self.gui.buttons_box.button(QtGui.QDialogButtonBox.Reset):
            self.slotResetButton()
        elif button == self.gui.buttons_box.button(QtGui.QDialogButtonBox.Cancel):
            self.slotCancelButton()
        else:
            self.slotOKButton()


    def slotResetButton(self):
        """
        Reset the Preferences dialog to the initial values.

        Settings selectors (text boxes, radio buttons, labels...) show
        their initial values when the ``Reset`` button is clicked.
        """
        # Ensure that no spurious values will be set in the application
        # if the user presses Reset followed by OK
        self.new_prefs = self.initial_prefs.copy()
        self.setPreferences(self.new_prefs)


    def slotCancelButton(self):
        """
        Reset the Preferences dialog to the initial values and close it.
        """

        self.new_prefs = self.initial_prefs.copy()
        for key, value in self.new_prefs.items():
            self.new_prefs[key] = QtCore.QVariant(value)
        self.gui.reject()


    def slotOKButton(self):
        """
        Apply the current preferences to the application and close the dialog.
        """

        for key, value in self.new_prefs.items():
            self.new_prefs[key] = QtCore.QVariant(value)
        self.gui.accept()


    def slotSetStartupDir(self, button_id):
        """
        Set the working directory of the application at startup.

        The working directory to be used at startup can be:

        - the home directory (this is the default)
        - the last directory opened by the application in the
        precedent session

        :Parameter button_id: a unique identifier of the checked radio button
        """

        for (key, value) in self.button2id.items():
            if value == button_id:
                self.new_prefs['Startup/startupWorkingDirectory'] = key


    def slotSetStartupSession(self, cb_on):
        """
        Set startup behavior of the application.

        If the Restore last session checkbox is checked then, at the
        next startup, the application will atempt to restore the last
        working session.

        :Parameter cb_on: a boolean indicator of the checkbox state.
        """

        if cb_on:
            self.new_prefs['Startup/restoreLastSession'] = 1
        else:
            self.new_prefs['Startup/restoreLastSession'] = 0


    def slotSetLoggerFont(self):
        """Set the logger font."""

        new_font, is_ok = QtGui.QFontDialog.getFont(self.gui.sample_te.font())
        # The selected font is applied to the sample text
        if is_ok:
            self.new_prefs['Logger/font'] = new_font
            self.gui.sample_te.setFont(new_font)


    def slotSetLoggerForeground(self):
        """Set the logger foreground color."""

        text_color = self.gui.sample_te.textColor()
        color = QtGui.QColorDialog.getColor(text_color)
        # The selected text color is applied to the sample text
        if color.isValid():
            self.new_prefs['Logger/text'] = color
            self.gui.sample_te.selectAll()
            self.gui.sample_te.setTextColor(color)
            self.gui.sample_te.moveCursor(QtGui.QTextCursor.End)


    def slotSetLoggerBackground(self):
        """Set the logger background color."""

        stylesheet = self.gui.sample_te.styleSheet()
        background = stylesheet[-7:]
        color = QtGui.QColorDialog.getColor(QtGui.QColor(background))
        # The selected paper color is applied to the sample text window
        if color.isValid():
            self.new_prefs['Logger/paper'] = color
            stylesheet.replace(background, color.name())
            self.gui.sample_te.setStyleSheet(stylesheet)


    def slotSetWorkspaceBackground(self):
        """Set the workspace background color."""

        stylesheet = self.gui.workspace_label.styleSheet()
        background = stylesheet[-7:]
        color = QtGui.QColorDialog.getColor(QtGui.QColor(background))
        # The selected color is applied to the sample label besides the button
        if color.isValid():
            self.new_prefs['Workspace/background'] = color
            stylesheet.replace(background, color.name())
            self.gui.workspace_label.setStyleSheet(stylesheet)


    def slotSetStyle(self, style_name):
        """
        Set the application style.

        :Parameter style_name: the style to be applied
        """
        self.new_prefs['Look/currentStyle'] = str(style_name)

