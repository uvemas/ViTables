# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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
This module provides a dialog for changing ``ViTables`` settings at runtime.

The dialog has 3 pages managed via QtGui.QStackedWidget: General settings 
page, Look&Feel settings page and Plugins settings page.
"""

__docformat__ = 'restructuredtext'

import os

from PyQt4 import QtCore
from PyQt4 import QtGui

from PyQt4.uic import loadUiType

from vitables.vtSite import ICONDIR
import vitables.utils

translate = QtGui.QApplication.translate
# This method of the PyQt4.uic module allows for dinamically loading user 
# interfaces created by QtDesigner. See the PyQt4 Reference Guide for more
# info.
Ui_SettingsDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__),'settings_dlg.ui'))[0]


class Preferences(QtGui.QDialog, Ui_SettingsDialog):
    """
    Create the Settings dialog.

    By loading UI files at runtime we can:

        - create user interfaces at runtime (without using pyuic)
        - use multiple inheritance, MyParentClass(BaseClass, FormClass)

    """

    def __init__(self):
        """
        Initialize the preferences dialog.

        * initializes the dialog appearance according to current preferences
        * connects dialog widgets to slots that provide them functionality
        """

        self.vtapp = vitables.utils.getVTApp()
        self.vtgui = self.vtapp.gui
        # Create the Settings dialog and customise it
        super(Preferences, self).__init__(self.vtgui)
        self.setupUi(self)

        self.config = self.vtapp.config
        self.pg_loader = self.vtapp.plugins_mgr
        self.plugins_paths = self.pg_loader.plugins_paths[:]
        self.enabled_plugins = self.pg_loader.enabled_plugins[:]

        # Setup the page selector widget
        self.setupIcons()

        # Style names can be retrieved with qt.QStyleFactory.keys()
        styles = QtGui.QStyleFactory.keys()
        self.stylesCB.insertItems(0, styles)

        # Setup the Plugins page
        self.enabled_model = QtGui.QStandardItemModel()
        self.enabledLV.setModel(self.enabled_model)
        self.disabled_model = QtGui.QStandardItemModel()
        self.disabledLV.setModel(self.disabled_model)
        self.paths_model = QtGui.QStandardItemModel()
        self.pathsLV.setModel(self.paths_model)
        for button in (self.removeButton, self.loadButton, 
            self.unloadButton):
            button.setEnabled(False)

        # The dictionary of current ViTables preferences
        self.initial_prefs = {}
        style_sheet = self.vtgui.logger.styleSheet()
        paper = style_sheet[-7:]
        self.initial_prefs['Logger/Paper'] = QtGui.QColor(paper)
        self.initial_prefs['Logger/Text'] = self.vtgui.logger.textColor()
        self.initial_prefs['Logger/Font'] = self.vtgui.logger.font()
        self.initial_prefs['Workspace/Background'] = \
            self.vtgui.workspace.background()
        self.initial_prefs['Look/currentStyle'] = self.config.current_style
        self.initial_prefs['Startup/startupWorkingDir'] = \
            self.config.startup_working_directory
        self.initial_prefs['Startup/restoreLastSession'] = \
            self.config.restore_last_session

        # The dictionary used to update the preferences
        self.new_prefs = {}

        # Apply the current ViTables configuration to the Preferences dialog
        self.resetPreferences()

        # Connect SIGNALS to SLOTS
        self.makeConnections()


    def setupIcons(self):
        """Setup icons in the selector list of the Preferences dialog.
        """

        iconsdir = os.path.join(ICONDIR, '64x64')
        general_button = QtGui.QListWidgetItem(self.contentsWidget)
        general_button.setIcon(QtGui.QIcon(os.path.join(iconsdir, 
            'preferences-other.png')))
        general_button.setText(translate('Preferences', "  General  ", 
            "Text for page selector icon"))
        general_button.setTextAlignment(QtCore.Qt.AlignHCenter)
        general_button.setFlags(QtCore.Qt.ItemIsSelectable | 
            QtCore.Qt.ItemIsEnabled)

        style_button = QtGui.QListWidgetItem(self.contentsWidget)
        style_button.setIcon(QtGui.QIcon(os.path.join(iconsdir, 
            'preferences-desktop-theme.png')))
        style_button.setText(translate('Preferences', "Look & Feel", 
            "Text for page selector icon"))
        style_button.setTextAlignment(QtCore.Qt.AlignHCenter)
        style_button.setFlags(QtCore.Qt.ItemIsSelectable | 
            QtCore.Qt.ItemIsEnabled)

        plugins_button = QtGui.QListWidgetItem(self.contentsWidget)
        plugins_button.setIcon(QtGui.QIcon(os.path.join(iconsdir, 
            'preferences-plugin.png')))
        plugins_button.setText(translate('Preferences', "  Plugins  ", 
            "Text for page selector icon"))
        plugins_button.setTextAlignment(QtCore.Qt.AlignHCenter)
        plugins_button.setFlags(QtCore.Qt.ItemIsSelectable | 
            QtCore.Qt.ItemIsEnabled)


    def resetPreferences(self):
        """
        Apply the current ``ViTables`` configuration to the Preferences dialog.
        """

        # Startup page
        if self.initial_prefs['Startup/startupWorkingDir'] == u'last':
            self.lastDirCB.setChecked(True)
        else:
            self.lastDirCB.setChecked(False)

        self.restoreCB.setChecked(\
            self.initial_prefs['Startup/restoreLastSession'])

        # Style page
        self.sampleTE.selectAll()
        self.sampleTE.setCurrentFont(self.initial_prefs['Logger/Font'])
        self.sampleTE.setTextColor(self.initial_prefs['Logger/Text'])
        self.sampleTE.moveCursor(QtGui.QTextCursor.End)  # Unselect text
        self.sampleTE.setStyleSheet(u"background-color: {0}".
            format(self.initial_prefs['Logger/Paper'].name()))

        self.workspaceLabel.setStyleSheet(u'background-color: {0}'.
            format(self.initial_prefs['Workspace/Background'].color().name()))

        index = self.stylesCB.findText(\
            self.initial_prefs['Look/currentStyle'])
        self.stylesCB.setCurrentIndex(index)

        # Plugins page
        self.setupList('paths', seq=self.pg_loader.plugins_paths)
        self.setupList('enabled', seq=self.pg_loader.enabled_plugins, 
            split=True)
        self.setupList('disabled', seq=self.pg_loader.disabled_plugins, 
            split=True)
        self.unloadButton.setEnabled(False)
        self.loadButton.setEnabled(False)

        # The visual update done above is not enough, we must reset the
        # new preferences dictionary and the lists of plugins paths and
        # enabled plugins
        self.new_prefs.clear()
        self.new_prefs.update(self.initial_prefs)
        self.plugins_paths = self.pg_loader.plugins_paths[:]
        self.enabled_plugins = self.pg_loader.enabled_plugins[:]


    def setupList(self, uid, seq, split=False):
        """Setup the plugins-related lists shown in the dialog.

        :Parameters:

        - `uid`: unique identifier for the list being setup
        - `seq`: the sequence of items to be added to the list
        - `split`: True if list items have the format folder#@#name
        """

        if uid == 'paths':
            view = self.pathsLV
        elif uid == 'enabled':
            view = self.enabledLV
        elif uid == 'disabled':
            view = self.disabledLV
        model = view.model()
        model.clear()
        for i in seq:
            if split:
                folder, name = i.split('#@#')
                item = QtGui.QStandardItem(name)
                item.setData(folder, QtCore.Qt.UserRole+1)
            else:
                item = QtGui.QStandardItem(i)
            model.appendRow(item)


    def makeConnections(self):
        """Connect signals to slots.

        The connections that cannot be done automatically by name are setup 
        here.
        """

        self.buttonsBox.helpRequested.connect(\
            QtGui.QWhatsThis.enterWhatsThisMode)

        # Plugins page
        self.disabledLV.selectionModel().selectionChanged.connect(\
            self.updateButton)
        self.enabledLV.selectionModel().selectionChanged.connect(\
            self.updateButton)
        self.pathsLV.selectionModel().selectionChanged.connect(\
            self.updateButton)



    @QtCore.pyqtSlot("QListWidgetItem *", "QListWidgetItem *", \
        name="on_contentsWidget_currentItemChanged")
    def changeSettingsPage(self, current, previous):
        """Slot for changing the selected page in the Settings dialog.

        :Parameters:

        - `current`: the item currently selected in the page selector widget
        - `previous`: the previous current item
        """
        if not current:
            current = previous

        self.stackedPages.setCurrentIndex(self.contentsWidget.row(current))


    @QtCore.pyqtSlot("QAbstractButton *", name="on_buttonsBox_clicked")
    def executeButtonAction(self, button):
        """Slot that manages button box clicks in the Preferences dialog.

        Whenever one of the `Help`, `Reset`, `Cancel` or `OK` buttons is
        clicked in the Preferences dialog this slot is called.

        :Parameter button: the clicked button.
        """

        if button == self.buttonsBox.button(QtGui.QDialogButtonBox.Reset):
            self.resetPreferences()
        elif button == self.buttonsBox.button(QtGui.QDialogButtonBox.Help):
            pass
        elif button == self.buttonsBox.button(QtGui.QDialogButtonBox.Cancel):
            self.reject()
        else:
            self.applySettings()


    def applySettings(self):
        """
        Apply the current preferences to the application and close the dialog.

        This method is a slot connected to the `accepted` signal. See
        ctor for details.
        """

        # Update the plugins manager
        self.pg_loader.plugins_paths = self.plugins_paths[:]
        self.pg_loader.enabled_plugins = self.enabled_plugins[:]
        self.pg_loader.register()

        # Update the rest of settings
        for key, value in self.new_prefs.items():
            self.new_prefs[key] = value

        self.accept()


    @QtCore.pyqtSlot("bool", name="on_lastDirCB_toggled")
    def setInitialWorkingDirectory(self, cb_on):
        """
        Configure startup behavior of the application.

        If the `Start in last opened directory` check box is checked
        then when the user opens a file *for the very first time* the
        current directory of the file selector dialog (CDFSD) will be
        the last directory accessed in the previous ``ViTables session``. If
        it is not checked then ``ViTables`` follows the standard behavior:
        if it has been started from a console session then the CDFSD
        will be the current working directory of the session, if it has
        been started from a menu/desktop-icon/run-command-applet the
        CDFSD will be the users' home.

        This is a slot method.

        :Parameter cb_on: a boolean indicator of the checkbox state.
        """

        if cb_on:
            self.new_prefs['Startup/startupWorkingDir'] = u'last'
        else:
            self.new_prefs['Startup/startupWorkingDir'] = u'home'


    @QtCore.pyqtSlot("bool", name="on_restoreCB_toggled")
    def setRestoreSession(self, cb_on):
        """
        Configure startup behavior of the application.

        If the `Restore last session` checkbox is checked then, at the
        next startup, the application will atempt to restore the last
        working session.

        This is a slot method.

        :Parameter cb_on: a boolean indicator of the checkbox state.
        """

        if cb_on:
            self.new_prefs['Startup/restoreLastSession'] = 1
        else:
            self.new_prefs['Startup/restoreLastSession'] = 0


    @QtCore.pyqtSlot(name="on_fontPB_clicked")
    def setLoggerFont(self):
        """Slot for setting the logger font."""

        new_font, is_ok = \
            QtGui.QFontDialog.getFont(self.sampleTE.currentFont())
        # The selected font is applied to the sample text
        if is_ok:
            self.new_prefs['Logger/Font'] = new_font
            self.sampleTE.selectAll()
            self.sampleTE.setCurrentFont(new_font)
            self.sampleTE.moveCursor(QtGui.QTextCursor.End)  # Unselect text


    @QtCore.pyqtSlot(name="on_foregroundPB_clicked")
    def setLoggerTextColor(self):
        """Slot for setting the logger foreground color."""

        text_color = self.sampleTE.textColor()
        color = QtGui.QColorDialog.getColor(text_color)
        # The selected text color is applied to the sample text
        if color.isValid():
            self.new_prefs['Logger/Text'] = color
            self.sampleTE.selectAll()
            self.sampleTE.setTextColor(color)
            self.sampleTE.moveCursor(QtGui.QTextCursor.End)


    @QtCore.pyqtSlot(name="on_backgroundPB_clicked")
    def setLoggerBackgroundColor(self):
        """Slot for setting the logger background color."""

        stylesheet = self.sampleTE.styleSheet()
        background = stylesheet[-7:]
        color = QtGui.QColorDialog.getColor(QtGui.QColor(background))
        # The selected paper color is applied to the sample text window
        if color.isValid():
            self.new_prefs['Logger/Paper'] = color
            new_stylesheet = stylesheet.replace(background, color.name())
            self.sampleTE.setStyleSheet(new_stylesheet)


    @QtCore.pyqtSlot(name="on_workspacePB_clicked")
    def setWorkspaceColor(self):
        """Slot for setting the workspace background color."""

        stylesheet = self.workspaceLabel.styleSheet()
        background = stylesheet[-7:]
        color = QtGui.QColorDialog.getColor(QtGui.QColor(background))
        # The selected color is applied to the sample label besides the button
        if color.isValid():
            self.new_prefs['Workspace/Background'] = QtGui.QBrush(color)
            new_stylesheet = stylesheet.replace(background, color.name())
            self.workspaceLabel.setStyleSheet(new_stylesheet)


    @QtCore.pyqtSlot("QString", name="on_stylesCB_activated")
    def setGlobalStyle(self, style_name):
        """
        Slot for setting the application style.

        :Parameter style_name: the style to be applied
        """
        self.new_prefs['Look/currentStyle'] = style_name


    @QtCore.pyqtSlot(name="on_newButton_clicked")
    def addSearchablePath(self):
        """Slot for adding a new searchable path if `New` button is clicked."""

        folder = QtGui.QFileDialog.getExistingDirectory()
        if not folder:
            return

        # Add the folder to the list of folders unless it is already there
        model = self.pathsLV.model()
        self.plugins_paths = [model.item(row).text() \
            for row in range(model.rowCount())]
        if not folder in self.plugins_paths:
            item = QtGui.QStandardItem(folder)
            model.appendRow(item)
            self.plugins_paths.append(folder)


    @QtCore.pyqtSlot(name="on_removeButton_clicked")
    def removeSearchablePath(self):
        """Slot for removing a searchable path if `Remove` button clicked."""

        current = self.pathsLV.currentIndex()
        model = self.pathsLV.model()
        model.removeRow(current.row(), current.parent())
        self.plugins_paths = [model.item(row).text() \
            for row in range(model.rowCount())]


    @QtCore.pyqtSlot(name="on_loadButton_clicked")
    def enablePlugin(self):
        """Slot for enabling a plugin if `Load` button clicked."""

        enabled_model = self.enabledLV.model()
        disabled_model = self.disabledLV.model()

        current_index = self.disabledLV.currentIndex()
        row = current_index.row()
        item = QtGui.QStandardItem(disabled_model.item(row))
        enabled_model.appendRow(item)
        disabled_model.removeRows(row, 1, current_index.parent())


        self.enabled_plugins = []
        for row in range(enabled_model.rowCount()):
            item = enabled_model.item(row)
            name = item.text()
            folder = item.data()
            self.enabled_plugins.append(u'{0}#@#{1}'.format(folder, name))


    @QtCore.pyqtSlot(name="on_unloadButton_clicked")
    def disablePlugin(self):
        """Slot for disabling a plugin if `Unload` button clicked."""

        enabled_model = self.enabledLV.model()
        disabled_model = self.disabledLV.model()

        current_index = self.enabledLV.currentIndex()
        row = current_index.row()
        item = QtGui.QStandardItem(enabled_model.item(row))
        enabled_model.removeRows(row, 1, current_index.parent())
        disabled_model.appendRow(item)

        self.enabled_plugins = []
        for row in range(enabled_model.rowCount()):
            item = enabled_model.item(row)
            name = item.text()
            folder = item.data()
            self.enabled_plugins.append(u'{0}#@#{1}'.format(folder, name))


    def updateButton(self, selected, deselected):
        """Enable/disable actions in the configuration dialog.

        This slot is called when a new item becomes selected in a list
        view (the plugins paths list, the enabled plugins list or the
        disabled plugins list) and updates the actions tied to that list.

        :Parameters:

        - `selected`: the item selection of selected items
        - `deselected`: the item selection of deselected items
        """

        selection_model = self.sender()
        model = selection_model.model()

        # Find out which button has to be updated
        if model == self.pathsLV.model():
            button = self.removeButton
        elif model == self.enabledLV.model():
            button = self.unloadButton
        elif model == self.disabledLV.model():
            button = self.loadButton

        # If the list is empty the button is disabled
        selected_indexes = selected.indexes()
        if selected_indexes == []:
            button.setEnabled(False)
            return

        # If an item is selected the button is enabled otherwise it is disabled
        if selection_model.hasSelection():
            button.setEnabled(True)
        else:
            button.setEnabled(False)
