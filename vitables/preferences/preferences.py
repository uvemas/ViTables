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
#       $Id: preferences.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the Preferences class.

Classes:

* Preferences(qt.QObject)

Methods:

* __init__(self, parent, current_prefs)
* __tr(self, source, comment=None)
* setPreferences(self, preferences)
* slotApplyButton(self)
* slotDefaultButton(self)
* slotSetStartupDir(self, button_id)
* slotSetStartupSession(self, cb_on)
* slotSetLoggerFont(self)
* slotSetLoggerForeground(self)
* slotSetLoggerBackground(self)
* slotSetWorkspaceBackground(self)
* slotSetStyle(self, style_name)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys

import qt

from vitables.preferences.vtconfig import Config
from vitables.preferences.preferencesGUI import PreferencesGUI

class Preferences(qt.QObject):
    """
    Gives functionality to the `Preferences` dialog.

    The `Preferences` dialog is a tabbed dialog with 2 pages, ``General``
    and ``Look&Feel``.
    In the ``General`` page the startup behavior can be configured.
    In the `Look&Feel`` page the configurable settings are:
    - font, foreground and background color of the logger
    - background color of the workspace
    - application style
    The dialog has ``OK``, ``Default``, ``Apply`` and ``Cancel`` buttons.
    They behave as usual.
    The class works as follows. Widgets used to set configurable values
    are connected to slots via suitable signals. The slots  store the
    property value in an instance variable. When ``Apply`` button is clicked
    these instances variables are passed to the application (that will
    process them somehow...). When the ``Default`` button is clicked the
    default values are read, applied to the dialog and stored in the
    instance variables.
    """

    def __init__(self, parent, current_prefs):
        """
        Initialize the preferences dialog.

        * initializes the GUI appearance according to current preferences
        * connects dialog widgets to slots that provide them functionality

        :Parameters:

        - `parent`: an instance of VTApp
        - `current_prefs`: a dictionary with current preferences
        """

        qt.QObject.__init__(self)

        # Radio button names are not usable, we need the numerical IDs
        self.button2id = {'home': 1, 'last': 2}

        self.vtapp = parent

        self.gui = PreferencesGUI()

        # A dictionary used to update the preferences
        self.new_prefs = {}.fromkeys(current_prefs.keys(), '')

        # Apply the current preferences to the dialog.
        # We make a copy in order to be sure that current_prefs will
        # remain unchanged. Changing it here will change it in
        # VTApp.slotToolsPreferences too and would make impossible to
        # recover the initial preferences if the Cancel button is clicked
        prefs = {}
        for key in current_prefs.keys():
            prefs[key] = current_prefs[key]
        self.setPreferences(prefs)

        # Connect SIGNALS to SLOTS
        # Apply, OK, Default buttons
        self.connect(self.gui, qt.SIGNAL('applyButtonPressed()'),
            self.slotApplyButton)
        self.connect(self.gui, qt.SIGNAL('defaultButtonPressed()'),
            self.slotDefaultButton)
        # Startup groupbox
        self.connect(self.gui.hiden_bg, qt.SIGNAL('clicked(int)'),
            self.slotSetStartupDir)
        self.connect(self.gui.restore_cb, qt.SIGNAL('toggled(bool)'),
            self.slotSetStartupSession)
        # Logger groupbox
        self.connect(self.gui.font_pb, qt.SIGNAL('clicked()'),
            self.slotSetLoggerFont)
        self.connect(self.gui.foreground_pb, qt.SIGNAL('clicked()'),
            self.slotSetLoggerForeground)
        self.connect(self.gui.background_pb, qt.SIGNAL('clicked()'),
            self.slotSetLoggerBackground)
        # Workspace groupbox
        self.connect(self.gui.workspace_pb, qt.SIGNAL('clicked()'),
            self.slotSetWorkspaceBackground)
        # Style groupbox
        self.connect(self.gui.styles_cb,
            qt.SIGNAL('activated(const QString &)'), self.slotSetStyle)


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('Preferences', source, comment).latin1()


    def setPreferences(self, preferences):
        """
        Applies a given set of preferences to the Preferences dialog.

        :Parameter preferences:
            a dictionary with current configuration settings
        """

        # Set the startup working directory
        rb_id = self.button2id[\
            preferences['Startup/startupWorkingDirectory']]
        self.gui.hiden_bg.setButton(rb_id)
        self.gui.restore_cb.setOn(\
            preferences['Startup/restoreLastSession'])
        # Look and Feel page
        self.gui.sample_te.selectAll()
        self.gui.sample_te.setFont(preferences['Logger/font'])
        self.gui.sample_te.setColor(preferences['Logger/text'])
        self.gui.sample_te.setPaper(qt.QBrush(\
            preferences['Logger/paper']))
        self.gui.sample_te.removeSelection()
        self.gui.workspace_label.setEraseColor(\
            preferences['Workspace/background'])
        self.gui.styles_cb.setCurrentText(\
            preferences['Look/currentStyle'])
        self.new_prefs = preferences


    #
    # slot methods
    #


    def slotApplyButton(self):
        """
        Apply the current preferences to the application.

        This method is called when the ``Apply`` button is clicked and
        also when the ``OK`` button is clicked.
        The changes made in the first case can be reverted with the
        ``Cancel`` button, which prevent the preferences saving. ``OK``
        button makes the changes permanent (for more details see
        `VTApp.slotToolsPreferences`).
        """
        self.vtapp.applyPreferences(self.new_prefs)


    def slotDefaultButton(self):
        """
        Apply the default preferences to the Preferences dialog.

        Settings selectors (text boxes, radio buttons, labels...) show
        their default values when the ``Default`` button is clicked.
        The default values are not automatically applied to the application.
        """

        preferences = {}
        for key in self.new_prefs.keys():
            preferences[key] = Config.confDef[key]

        # Apply the default configuration to the Preferences dialog
        rb_id = self.button2id[\
            preferences['Startup/startupWorkingDirectory']]
        self.gui.hiden_bg.setButton(rb_id)
        self.gui.restore_cb.setOn(preferences['Startup/restoreLastSession'])

        # Select the logger content in order to update it
        self.gui.sample_te.selectAll()
        # background
        self.gui.sample_te.setPaper(qt.QBrush(\
            preferences['Logger/paper']))
        # foreground
        self.gui.sample_te.setColor(preferences['Logger/text'])
        # font
        self.gui.sample_te.setFont(preferences['Logger/font'])
        # Remove the selection once the update is done
        self.gui.sample_te.removeSelection()

        # The workspace
        self.gui.workspace_label.setEraseColor(\
            preferences['Workspace/background'])

        # Application style
        self.gui.styles_cb.setCurrentText(preferences['Look/currentStyle'])

        # If the OK/Apply buttons are clicked after the Default button
        # then the default configuration will be applied to the main window
        self.new_prefs = preferences


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
        self.gui.restore_cb.setOn(self.new_prefs['Startup/restoreLastSession'])


    def slotSetLoggerFont(self):
        """Set the logger font."""

        (new_font, font_ok) = qt.QFontDialog.getFont(self.gui.sample_te.font())
        # The selected font is applied to the sample text
        if font_ok:
            self.new_prefs['Logger/font'] = new_font
            self.gui.sample_te.selectAll()
            self.gui.sample_te.setFont(new_font)
            self.gui.sample_te.removeSelection()
        else:
            # The user has cancelled the dialog, do nothing
            pass


    def slotSetLoggerForeground(self):
        """Set the logger foreground color."""

        color = qt.QColorDialog.getColor(self.gui.sample_te.color())
        # The selected text color is applied to the sample text
        if color.isValid():
            self.new_prefs['Logger/text'] = color
            self.gui.sample_te.selectAll()
            self.gui.sample_te.setColor(color)
            self.gui.sample_te.removeSelection()
        else:
            # The user has cancelled the dialog, do nothing
            pass


    def slotSetLoggerBackground(self):
        """Set the logger background color."""

        color = qt.QColorDialog.getColor(self.gui.sample_te.paper().color())
        # The selected paper color is applied to the sample text window
        if color.isValid():
            self.new_prefs['Logger/paper'] = color
            self.gui.sample_te.setPaper(qt.QBrush(color))
        else:
            # The user has cancelled the dialog, do nothing
            pass


    def slotSetWorkspaceBackground(self):
        """Set the workspace background color."""

        color = qt.QColorDialog.getColor(self.gui.workspace_label.eraseColor())
        # The selected color is applied to the sample label besides the button
        if color.isValid():
            self.new_prefs['Workspace/background'] = color
            self.gui.workspace_label.setEraseColor(color)
        else:
            # The user has cancelled the dialog, do nothing
            pass


    def slotSetStyle(self, style_name):
        """
        Set the application style.

        Style can be one of the following:
        - Platinum
        - Windows
        - Motif
        - MotifPlus
        - SGI
        - CDE

        :Parameter style_name: the style to be applied
        """
        self.new_prefs['Look/currentStyle'] = style_name.latin1()

if __name__ == '__main__':
    current_config = {}
    # Logger
    current_config['Logger/paper'] = qt.QBrush(qt.QColor('white'))
    current_config['Logger/text'] = qt.QColor('black')
    current_config['Logger/font'] = qt.QFont('Helvetica', 12, -1)
    # Workspace
    current_config['Workspace/background'] = qt.QColor('white')
    # Style
    current_config['Look/currentStyle'] = 'default'
    # Startup
    current_config['Startup/startupWorkingDirectory'] = 'home'
    current_config['Startup/restoreLastSession'] = 1
    app = qt.QApplication(sys.argv)
    prefs = Preferences(None, current_config)
    app.setMainWidget(prefs.gui)
    prefs.gui.show()
    app.exec_loop()

