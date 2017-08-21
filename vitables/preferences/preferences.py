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
This module provides a dialog for changing ``ViTables`` settings at runtime.

The dialog has 3 pages managed via QtGui.QStackedWidget: General settings
page, Look&Feel settings page and Plugins settings page.
"""

import os

from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from qtpy.uic import loadUiType

from vitables.vtsite import ICONDIR
import vitables.utils


__docformat__ = 'restructuredtext'

translate = QtWidgets.QApplication.translate
# This method of the PyQt5.uic module allows for dynamically loading user
# interfaces created by QtDesigner. See the PyQt5 Reference Guide for more
# info.
Ui_SettingsDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__), 'settings_dlg.ui'))[0]


class Preferences(QtWidgets.QDialog, Ui_SettingsDialog):
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
        # Create the Settings dialog and customize it
        super(Preferences, self).__init__(self.vtgui)
        self.setupUi(self)

        self.config = self.vtapp.config
        self.pg_loader = self.vtapp.plugins_mgr
        self.all_plugins = \
            dict(item for item in self.pg_loader.all_plugins.items())
        self.enabled_plugins = self.pg_loader.enabled_plugins[:]

        # Setup the Plugins page
        self.setupPluginsPage()

        # Setup the page selector widget
        self.setupSelector()

        # Display the General Settings page
        self.stackedPages.setCurrentIndex(0)

        # Style names can be retrieved with qt.QStyleFactory.keys()
        styles = QtWidgets.QStyleFactory.keys()
        self.stylesCB.insertItems(0, styles)

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
        self.initial_prefs['Session/startupWorkingDir'] = \
            self.config.initial_working_directory
        self.initial_prefs['Session/restoreLastSession'] = \
            self.config.restore_last_session

        # The dictionary used to update the preferences
        self.new_prefs = {}

        # Apply the current ViTables configuration to the Preferences dialog
        self.resetPreferences()

        # Connect SIGNALS to SLOTS
        self.buttonsBox.helpRequested.connect(
            QtWidgets.QWhatsThis.enterWhatsThisMode)

    def setupPluginsPage(self):
        """Populate the tree of plugins.
        """

        nrows = len(self.all_plugins)
        self.plugins_model = QtGui.QStandardItemModel(nrows, 2, self)
        self.pluginsTV.setModel(self.plugins_model)
        header = QtWidgets.QHeaderView(QtCore.Qt.Horizontal, self.pluginsTV)
        header.setStretchLastSection(True)
        self.pluginsTV.setHeader(header)
        self.plugins_model.setHorizontalHeaderLabels(['Name', 'Comment'])

        # Populate the model
        row = 0
        for UID, desc in self.all_plugins.items():
            name = desc['name']
            comment = desc['comment']
            nitem = QtGui.QStandardItem(name)
            nitem.setData(UID)
            nitem.setCheckable(True)
            if UID in self.enabled_plugins:
                nitem.setCheckState(QtCore.Qt.Checked)
            citem = QtGui.QStandardItem(comment)
            self.plugins_model.setItem(row, 0, nitem)
            self.plugins_model.setItem(row, 1, citem)
            row = row + 1

    def setupSelector(self):
        """Setup the page selector widget of the Preferences dialog.
        """

        iconsdir = os.path.join(ICONDIR, '64x64')
        self.selector_model = QtGui.QStandardItemModel(self)
        self.pageSelector.setModel(self.selector_model)

        # Populate the model with top level items
        alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        flags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        general_item = QtGui.QStandardItem()
        general_item.setIcon(QtGui.QIcon(os.path.join(
            iconsdir, 'preferences-other.png')))
        general_item.setText(translate('Preferences', "  General  ",
                                       "Text for page selector icon"))
        general_item.setTextAlignment(alignment)
        general_item.setFlags(flags)

        style_item = QtGui.QStandardItem()
        style_item.setIcon(QtGui.QIcon(os.path.join(
            iconsdir, 'preferences-desktop-theme.png')))
        style_item.setText(translate('Preferences', "Look & Feel",
                                     "Text for page selector icon"))
        style_item.setTextAlignment(alignment)
        style_item.setFlags(flags)

        self.plugins_item = QtGui.QStandardItem()
        self.plugins_item.setIcon(QtGui.QIcon(os.path.join(
            iconsdir, 'preferences-plugin.png')))
        self.plugins_item.setText(translate('Preferences', "  Plugins  ",
                                            "Text for page selector icon"))
        self.plugins_item.setTextAlignment(alignment)
        self.plugins_item.setFlags(flags)

        for item in (general_item, style_item, self.plugins_item):
            self.selector_model.appendRow(item)

        # Add items for *loaded* plugins to the Plugins item
        index = self.selector_model.indexFromItem(self.plugins_item)
        self.pageSelector.setExpanded(index, True)
        for UID in self.vtapp.plugins_mgr.loaded_plugins.keys():
            name = UID.split('#@#')[0]
            item = QtGui.QStandardItem(name)
            item.setData(UID)
            self.plugins_item.appendRow(item)

    @QtCore.Slot("QModelIndex", name="on_pageSelector_clicked")
    def changeSettingsPage(self, index):
        """Slot for changing the selected page in the Settings dialog.

        :Parameter index: the index clicked by the user
        """

        # If top level item is clicked
        if not index.parent().isValid():
            self.stackedPages.setCurrentIndex(index.row())
        # If a plugin item is clicked
        elif index.parent() == self.plugins_item.index():
            pluginID = self.selector_model.itemFromIndex(index).data()
            self.aboutPluginPage(pluginID)

    @QtCore.Slot("QAbstractButton *", name="on_buttonsBox_clicked")
    def executeButtonAction(self, button):
        """Slot that manages button box clicks in the Preferences dialog.

        Whenever one of the `Help`, `Reset`, `Cancel` or `OK` buttons is
        clicked in the Preferences dialog this slot is called.

        :Parameter button: the clicked button.
        """

        if button == self.buttonsBox.button(QtWidgets.QDialogButtonBox.Reset):
            self.resetPreferences()
        elif button == self.buttonsBox.button(QtWidgets.QDialogButtonBox.Help):
            pass
        elif button == self.buttonsBox.button(
                QtWidgets.QDialogButtonBox.Cancel):
            self.reject()
        else:
            self.applySettings()

    def resetPreferences(self):
        """
        Apply the current ``ViTables`` configuration to the Preferences dialog.
        """

        # Startup page
        if self.initial_prefs['Session/startupWorkingDir'] == 'last':
            self.lastDirCB.setChecked(True)
        else:
            self.lastDirCB.setChecked(False)

        self.restoreCB.setChecked(
            self.initial_prefs['Session/restoreLastSession'])

        # Style page
        self.sampleTE.selectAll()
        self.sampleTE.setCurrentFont(self.initial_prefs['Logger/Font'])
        self.sampleTE.setTextColor(self.initial_prefs['Logger/Text'])
        self.sampleTE.moveCursor(QtGui.QTextCursor.End)  # Unselect text
        self.sampleTE.setStyleSheet("background-color: {0}".format(
            self.initial_prefs['Logger/Paper'].name()))

        self.workspaceLabel.setStyleSheet('background-color: {0}'.format(
            self.initial_prefs['Workspace/Background'].color().name()))

        index = self.stylesCB.findText(self.initial_prefs['Look/currentStyle'])
        self.stylesCB.setCurrentIndex(index)

        # The visual update done above is not enough, we must reset the
        # new preferences dictionary and the list of enabled plugins
        self.new_prefs.clear()
        self.new_prefs.update(self.initial_prefs)
        self.enabled_plugins = self.pg_loader.enabled_plugins[:]
        self.all_plugins = \
            dict(item for item in self.pg_loader.all_plugins.items())
#        UIDs = self.all_plugins.keys()
        for row in range(0, self.plugins_model.rowCount()):
            item = self.plugins_model.item(row, 0)
            if item.data() in self.enabled_plugins:
                item.setCheckState(2)
            else:
                item.setCheckState(0)

    def applySettings(self):
        """
        Apply the current preferences to the application and close the dialog.

        This method is a slot connected to the `accepted` signal. See
        ctor for details.
        """

        # Update the plugins manager
        self.updatePluginsManager()

        # Update the rest of settings
        for key, value in self.new_prefs.items():
            self.new_prefs[key] = value

        self.accept()

    @QtCore.Slot("bool", name="on_lastDirCB_toggled")
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
            self.new_prefs['Session/startupWorkingDir'] = 'last'
        else:
            self.new_prefs['Session/startupWorkingDir'] = 'home'

    @QtCore.Slot("bool", name="on_restoreCB_toggled")
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
            self.new_prefs['Session/restoreLastSession'] = True
        else:
            self.new_prefs['Session/restoreLastSession'] = False

    @QtCore.Slot(name="on_fontPB_clicked")
    def setLoggerFont(self):
        """Slot for setting the logger font."""

        new_font, is_ok = \
            QtWidgets.QFontDialog.getFont(self.sampleTE.currentFont())
        # The selected font is applied to the sample text
        if is_ok:
            self.new_prefs['Logger/Font'] = new_font
            self.sampleTE.selectAll()
            self.sampleTE.setCurrentFont(new_font)
            self.sampleTE.moveCursor(QtGui.QTextCursor.End)  # Unselect text

    @QtCore.Slot(name="on_foregroundPB_clicked")
    def setLoggerTextColor(self):
        """Slot for setting the logger foreground color."""

        text_color = self.sampleTE.textColor()
        color = QtWidgets.QColorDialog.getColor(text_color)
        # The selected text color is applied to the sample text
        if color.isValid():
            self.new_prefs['Logger/Text'] = color
            self.sampleTE.selectAll()
            self.sampleTE.setTextColor(color)
            self.sampleTE.moveCursor(QtGui.QTextCursor.End)

    @QtCore.Slot(name="on_backgroundPB_clicked")
    def setLoggerBackgroundColor(self):
        """Slot for setting the logger background color."""

        stylesheet = self.sampleTE.styleSheet()
        background = stylesheet[-7:]
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(background))
        # The selected paper color is applied to the sample text window
        if color.isValid():
            self.new_prefs['Logger/Paper'] = color
            new_stylesheet = stylesheet.replace(background, color.name())
            self.sampleTE.setStyleSheet(new_stylesheet)

    @QtCore.Slot(name="on_workspacePB_clicked")
    def setWorkspaceColor(self):
        """Slot for setting the workspace background color."""

        stylesheet = self.workspaceLabel.styleSheet()
        background = stylesheet[-7:]
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(background))
        # The selected color is applied to the sample label besides the button
        if color.isValid():
            self.new_prefs['Workspace/Background'] = QtGui.QBrush(color)
            new_stylesheet = stylesheet.replace(background, color.name())
            self.workspaceLabel.setStyleSheet(new_stylesheet)

    @QtCore.Slot("QString", name="on_stylesCB_activated")
    def setGlobalStyle(self, style_name):
        """
        Slot for setting the application style.

        :Parameter style_name: the style to be applied
        """
        self.new_prefs['Look/currentStyle'] = style_name

    def updatePluginsManager(self):
        """Update the plugins manager before closing the dialog.

        When the Apply button is clicked the list of enabled plugins
        is refreshed.
        """

        self.enabled_plugins = []
        for row in range(self.plugins_model.rowCount()):
            item = self.plugins_model.item(row, 0)
            if item.checkState() == 2:
                self.enabled_plugins.append(item.data())

        self.pg_loader.enabled_plugins = self.enabled_plugins[:]

    def aboutPluginPage(self, pluginID):
        """A page with info about the plugin clicked in the selector widget.

        :Parameter pluginID: a unique ID for getting the proper plugin
        """

        # Refresh the Preferences dialog pages. There is at most one
        # About Plugin page at any given time
        while self.stackedPages.count() > 3:
            about_page = self.stackedPages.widget(3)
            self.stackedPages.removeWidget(about_page)
            del about_page

        pg_instance = self.vtapp.plugins_mgr.loaded_plugins[pluginID]
        try:
            about_page = pg_instance.helpAbout(self.stackedPages)
        except AttributeError:
            about_page = QtWidgets.QWidget(self.stackedPages)
            label = QtWidgets.QLabel(translate(
                'Preferences',
                'Sorry, there are no info available for this plugin',
                'A text label'), about_page)
            layout = QtWidgets.QVBoxLayout(about_page)
            layout.addWidget(label)

        self.stackedPages.addWidget(about_page)
        self.stackedPages.setCurrentIndex(3)
