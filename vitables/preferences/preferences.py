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

"""
Here is defined the Preferences class.

Classes:

* Preferences(QtGui.QDialog, settingsUI.Ui_SettingsDialog)

Methods:

* __init__(self, vtapp)
* setPreferences(self, preferences)
* slotButtonClicked(self, button)
* slotResetButton(self)
* slotOKButton(self)
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
_context = 'Preferences'

import os

from PyQt4 import QtCore, QtGui

from vitables.preferences import settingsUI
from vitables.vtSite import ICONDIR
import vitables.utils


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


class Preferences(QtGui.QDialog, settingsUI.Ui_SettingsDialog):
    """
    Create the Settings dialog.
    """

    def __init__(self):
        """
        Initialize the preferences dialog.

        * initializes the GUI appearance according to current preferences
        * connects dialog widgets to slots that provide them functionality
        """

        self.vtapp = vitables.utils.getVTApp()
        # Create the Settings dialog and customise it
        QtGui.QDialog.__init__(self, self.vtapp)
        self.setupUi(self)

        self.config = self.vtapp.config
        self.pg_loader = self.vtapp.plugins_mgr
        self.plugins_paths = self.pg_loader.plugins_paths[:]
        self.enabled_plugins = self.pg_loader.enabled_plugins[:]

        # Setup the page selector widget
        self.setupIcons()
        self.contents_widget.setMovement(QtGui.QListView.Static)
        self.contents_widget.setMaximumWidth(120)
        self.contents_widget.setSpacing(12)

        # Set the sample text in the Logger groupbox
        text = """<p>En un lugar de La Mancha,<br>""" \
        """de cuyo nombre no quiero acordarme,<br>""" \
        """no ha mucho tiempo vivia un hidalgo...</p>"""
        self.sample_te.setText(text)

        # Style names can be retrieved with qt.QStyleFactory.keys()
        styles = QtGui.QStyleFactory.keys()
        self.styles_cb.insertItems(0, styles)

        # Setup the Plugins page
        self.enabled_model = QtGui.QStandardItemModel()
        self.enabled_lv.setModel(self.enabled_model)
        self.disabled_model = QtGui.QStandardItemModel()
        self.disabled_lv.setModel(self.disabled_model)
        self.paths_model = QtGui.QStandardItemModel()
        self.paths_lv.setModel(self.paths_model)
        for button in (self.remove_button, self.load_button, 
            self.unload_button):
            button.setEnabled(False)

        # The current preferences of the application
        self.initial_prefs = {}
        style_sheet = self.vtapp.logger.styleSheet()
        paper = style_sheet[-7:]
        self.initial_prefs['Logger/Paper'] = QtGui.QColor(paper)
        self.initial_prefs['Logger/Text'] = self.vtapp.logger.textColor()
        self.initial_prefs['Logger/Font'] = self.vtapp.logger.font()
        self.initial_prefs['Workspace/Background'] = \
            self.vtapp.workspace.background()
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
        general_button = QtGui.QListWidgetItem(self.contents_widget)
        general_button.setIcon(QtGui.QIcon(os.path.join(iconsdir, 
            'preferences-other.png')))
        general_button.setText(trs("  General  ", 
            "Text for page selector icon"))
        general_button.setTextAlignment(QtCore.Qt.AlignHCenter)
        general_button.setFlags(QtCore.Qt.ItemIsSelectable | 
            QtCore.Qt.ItemIsEnabled)

        style_button = QtGui.QListWidgetItem(self.contents_widget)
        style_button.setIcon(QtGui.QIcon(os.path.join(iconsdir, 
            'preferences-desktop-theme.png')))
        style_button.setText(trs("Look & Feel", "Text for page selector icon"))
        style_button.setTextAlignment(QtCore.Qt.AlignHCenter)
        style_button.setFlags(QtCore.Qt.ItemIsSelectable | 
            QtCore.Qt.ItemIsEnabled)

        plugins_button = QtGui.QListWidgetItem(self.contents_widget)
        plugins_button.setIcon(QtGui.QIcon(os.path.join(iconsdir, 
            'preferences-plugin.png')))
        plugins_button.setText(trs("  Plugins  ", 
            "Text for page selector icon"))
        plugins_button.setTextAlignment(QtCore.Qt.AlignHCenter)
        plugins_button.setFlags(QtCore.Qt.ItemIsSelectable | 
            QtCore.Qt.ItemIsEnabled)


    def resetPreferences(self):
        """
        Apply the current ViTables configuration to the Preferences dialog.
        """

        # Startup page
        if self.initial_prefs['Startup/startupWorkingDir'] == u'last':
            self.last_dir_cb.setChecked(True)
        else:
            self.last_dir_cb.setChecked(False)

        self.restore_cb.setChecked(\
            self.initial_prefs['Startup/restoreLastSession'])

        # Style page
        self.sample_te.selectAll()
        self.sample_te.setTextColor(self.initial_prefs['Logger/Text'])
        self.sample_te.moveCursor(QtGui.QTextCursor.End)  # Unselect text
        self.sample_te.setStyleSheet("""background-color: %s""" % 
            self.initial_prefs['Logger/Paper'].name())
        self.sample_te.setFont(self.initial_prefs['Logger/Font'])

        self.workspace_label.setStyleSheet('background-color: %s' % 
            self.initial_prefs['Workspace/Background'].color().name())

        index = self.styles_cb.findText(\
            self.initial_prefs['Look/currentStyle'])
        self.styles_cb.setCurrentIndex(index)

        # Plugins page
        self.setupList('paths', seq=self.pg_loader.plugins_paths)
        self.setupList('enabled', seq=self.pg_loader.enabled_plugins, 
            split=True)
        self.setupList('disabled', seq=self.pg_loader.disabled_plugins, 
            split=True)


    def setupList(self, uid, seq, split=False):
        """Setup the list shown in the dialog.

        :Parameters:

        - `uid`: unique identifier for the list being setup
        - `seq`: the sequence of items to be added to the list
        - `split`: True if list items have the format folder#@#name
        """

        if uid == 'paths':
            view = self.paths_lv
        elif uid == 'enabled':
            view = self.enabled_lv
        elif uid == 'disabled':
            view = self.disabled_lv
        model = view.model()
        model.clear()
        for i in seq:
            if split:
                folder, name = i.split('#@#')
                item = QtGui.QStandardItem(name)
                item.setData(QtCore.QVariant(folder), QtCore.Qt.UserRole+1)
            else:
                item = QtGui.QStandardItem(i)
            model.appendRow(item)


    def makeConnections(self):
        """Connect signals to slots.

        There is a bunch of connections to stablish so I've moved them to
        their own method just for clarity.
        """

        # Apply, OK, Reset and Cancel buttons
        self.connect(self.buttons_box, 
            QtCore.SIGNAL('clicked(QAbstractButton *)'),
            self.buttonClicked)

        # Selector widget
        self.connect(self.contents_widget, 
            QtCore.SIGNAL(\
                'currentItemChanged(QListWidgetItem *, QListWidgetItem *)'), 
            self.changePage)

        # General page
        self.connect(self.last_dir_cb, QtCore.SIGNAL('toggled(bool)'),
            self.startupDir)
        self.connect(self.restore_cb, QtCore.SIGNAL('toggled(bool)'),
            self.startupSession)

        # Style page
        self.connect(self.font_pb, QtCore.SIGNAL('clicked()'),
            self.loggerFont)
        self.connect(self.foreground_pb, QtCore.SIGNAL('clicked()'),
            self.loggerForeground)
        self.connect(self.background_pb, QtCore.SIGNAL('clicked()'),
            self.loggerBackground)
        self.connect(self.workspace_pb, QtCore.SIGNAL('clicked()'),
            self.workspaceBackground)
        self.connect(self.styles_cb,
            QtCore.SIGNAL('activated(QString)'), self.style)

        # Plugins page
        self.connect(self.buttons_box, QtCore.SIGNAL('helpRequested()'),
            QtGui.QWhatsThis.enterWhatsThisMode)
        self.connect(self.new_button, QtCore.SIGNAL('clicked()'), 
            self.addPath)
        self.connect(self.remove_button, QtCore.SIGNAL('clicked()'),
            self.removePath)
        self.connect(self.load_button, QtCore.SIGNAL('clicked()'),
            self.enablePlugin)
        self.connect(self.unload_button, QtCore.SIGNAL('clicked()'),
            self.disablePlugin)
        current_changed = \
            QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)')
        self.connect(self.disabled_lv.selectionModel(), current_changed, 
            self.updateButton)
        self.connect(self.enabled_lv.selectionModel(), current_changed, 
            self.updateButton)
        self.connect(self.paths_lv.selectionModel(), current_changed, 
            self.updateButton)


    def changePage(self, current, previous):
        """Change the selected page in the Settings dialog.

        This method is a slot connected to the `currentItemChanged` signal.
        See ctor for details.

        :Parameters:

        - `current`: the item currently selected in the page selector widget
        - `previous`: the previous current item
        """
        if not current:
            current = previous

        self.pages_widget.setCurrentIndex(self.contents_widget.row(current))


    def buttonClicked(self, button):
        """Manages dialog button cliks in the Preferences dialog.

        Whenever one of the Help, Reset, Cancel or OK buttons is
        clicked in the Preferences dialog this slot is called.

        This method is a slot. See the makeConnections method for details.

        :Parameter button: the clicked button.
        """

        if button == self.buttons_box.button(QtGui.QDialogButtonBox.Reset):
            self.resetPreferences()
        elif button == self.buttons_box.button(QtGui.QDialogButtonBox.Help):
            pass
        elif button == self.buttons_box.button(QtGui.QDialogButtonBox.Cancel):
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
            self.new_prefs[key] = QtCore.QVariant(value)

        self.accept()


    def startupDir(self, cb_on):
        """
        Set startup behavior of the application.

        If the `Start in last opened directory` check box is checked
        then when the user opens a file *for the very first time* the
        current directory of the file selector dialog (CDFSD) will be
        the last directory accessed in the previous ViTables session. If
        it is not checked then ViTables follows the standard behavior:
        if it has been started from a console session then the CDFSD
        will be the current working directory of the session, if it has
        been started from a menu/desktop-icon/run-command-applet the
        CDFSD will be the users home.

        This method is a slot. See the makeConnections method for details.

        :Parameter cb_on: a boolean indicator of the checkbox state.
        """

        if cb_on:
            self.new_prefs['Startup/startupWorkingDir'] = u'last'
        else:
            self.new_prefs['Startup/startupWorkingDir'] = u'home'


    def startupSession(self, cb_on):
        """
        Set startup behavior of the application.

        If the Restore last session checkbox is checked then, at the
        next startup, the application will atempt to restore the last
        working session.

        This method is a slot. See the makeConnections method for details.

        :Parameter cb_on: a boolean indicator of the checkbox state.
        """

        if cb_on:
            self.new_prefs['Startup/restoreLastSession'] = 1
        else:
            self.new_prefs['Startup/restoreLastSession'] = 0


    def loggerFont(self):
        """Set the logger font.

        This method is a slot. See the makeConnections method for details.
        """

        new_font, is_ok = QtGui.QFontDialog.getFont(self.sample_te.font())
        # The selected font is applied to the sample text
        if is_ok:
            self.new_prefs['Logger/Font'] = new_font
            self.sample_te.setFont(new_font)


    def loggerForeground(self):
        """Set the logger foreground color.

        This method is a slot. See the makeConnections method for details.
        """

        text_color = self.sample_te.textColor()
        color = QtGui.QColorDialog.getColor(text_color)
        # The selected text color is applied to the sample text
        if color.isValid():
            self.new_prefs['Logger/Text'] = color
            self.sample_te.selectAll()
            self.sample_te.setTextColor(color)
            self.sample_te.moveCursor(QtGui.QTextCursor.End)


    def loggerBackground(self):
        """Set the logger background color.

        This method is a slot. See the makeConnections method for details.
        """

        stylesheet = self.sample_te.styleSheet()
        background = stylesheet[-7:]
        color = QtGui.QColorDialog.getColor(QtGui.QColor(background))
        # The selected paper color is applied to the sample text window
        if color.isValid():
            self.new_prefs['Logger/Paper'] = color
            stylesheet.replace(background, color.name())
            self.sample_te.setStyleSheet(stylesheet)


    def workspaceBackground(self):
        """Set the workspace background color.

        This method is a slot. See the makeConnections method for details.
        """

        stylesheet = self.workspace_label.styleSheet()
        background = stylesheet[-7:]
        color = QtGui.QColorDialog.getColor(QtGui.QColor(background))
        # The selected color is applied to the sample label besides the button
        if color.isValid():
            self.new_prefs['Workspace/Background'] = QtGui.QBrush(color)
            stylesheet.replace(background, color.name())
            self.workspace_label.setStyleSheet(stylesheet)


    def style(self, style_name):
        """
        Set the application style.

        This method is a slot. See the makeConnections method for details.

        :Parameter style_name: the style to be applied
        """
        self.new_prefs['Look/currentStyle'] = unicode(style_name)


    def addPath(self):
        """New button clicked.

        This method is a slot. See the makeConnections method for details.
        """

        folder = QtGui.QFileDialog.getExistingDirectory()
        folder = unicode(folder)
        if not folder:
            return

        # Add the folder to the list of folders unless it is already there
        model = self.paths_lv.model()
        self.plugins_paths = [unicode(model.item(row).text()) \
            for row in range(model.rowCount())]
        if not folder in self.plugins_paths:
            item = QtGui.QStandardItem(folder)
            model.appendRow(item)
            self.plugins_paths.append(folder)


    def removePath(self):
        """Remove button clicked.

        This method is a slot. See the makeConnections method for details.
        """

        current = self.paths_lv.currentIndex()
        model = self.paths_lv.model()
        model.removeRow(current.row(), current.parent())
        self.plugins_paths = [unicode(model.item(row).text()) \
            for row in range(model.rowCount())]


    def enablePlugin(self):
        """Load button clicked.

        This method is a slot. See the makeConnections method for details.
        """

        enabled_model = self.enabled_lv.model()
        disabled_model = self.disabled_lv.model()

        current_index = self.disabled_lv.currentIndex()
        row = current_index.row()
        item = QtGui.QStandardItem(disabled_model.item(row))
        enabled_model.appendRow(item)
        disabled_model.removeRows(row, 1, current_index.parent())


        self.enabled_plugins = []
        for row in range(enabled_model.rowCount()):
            item = enabled_model.item(row)
            name = unicode(item.text())
            folder = unicode(item.data().toString())
            self.enabled_plugins.append('%s#@#%s' % (folder, name))


    def disablePlugin(self):
        """Unload button clicked.

        This method is a slot. See the makeConnections method for details.
        """

        enabled_model = self.enabled_lv.model()
        disabled_model = self.disabled_lv.model()

        current_index = self.enabled_lv.currentIndex()
        row = current_index.row()
        item = QtGui.QStandardItem(enabled_model.item(row))
        enabled_model.removeRows(row, 1, current_index.parent())
        disabled_model.appendRow(item)

        self.enabled_plugins = []
        for row in range(enabled_model.rowCount()):
            item = enabled_model.item(row)
            name = unicode(item.text())
            folder = unicode(item.data().toString())
            self.enabled_plugins.append('%s#@#%s' % (folder, name))


    def updateButton(self, selected, deselected):
        """Enable/disable actions in the configuration dialog.

        This slot is called when a new item becomes selected in a list
        view (the plugins paths list, the enabled plugins list or the
        disabled plugins list) and updates the actions tied to that list.

        :Parameters:
        - `current`: the new current model index
        - `previous`: the previous current model index
        """

        selection_model = self.sender()
        model = selection_model.model()

        # Find out which button has to be updated
        if model == self.paths_lv.model():
            button = self.remove_button
        elif model == self.enabled_lv.model():
            button = self.unload_button
        elif model == self.disabled_lv.model():
            button = self.load_button

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
