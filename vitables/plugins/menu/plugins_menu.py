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

"""This plugin creates a `Plugins` menu and adds an item to it for each 
active plugin. Selecting these menu items will bring up a short 
`About Plugin` dialog with the details of the plugin.
"""

__docformat__ = 'restructuredtext'
__version__ = '0.2'
plugin_class = 'PluginsMenu'

import os

from PyQt4 import QtCore
from PyQt4 import QtGui


import vitables.utils
from vitables.vtSite import PLUGINSDIR

translate = QtGui.QApplication.translate


def setupTextWidget(parent, palette, kind='line'):
    """Create and setup a text editor widget.

    :Parameters:

    - `parent`: the parent widget of the widget being created
    - `palette`: the `QPalette` used by the editor widget being created
    - `kind`: the kind of editor widget being created (single-line editor or
      multiline editor)
    """

    if kind == 'line':
        widget = QtGui.QLineEdit(parent)
    else:
        widget = QtGui.QTextEdit(parent)
    widget.setReadOnly(True)
    widget.setPalette(palette)
    return widget


class PluginsMenu(QtCore.QObject):
    """Add a `Plugins` menu to the ``ViTables`` menubar.
    """

    def __init__(self):
        """The class constructor.
        """

        super(PluginsMenu, self).__init__()

        # Get a reference to the application instance
        self.vtapp = vitables.utils.getVTApp()
        if self.vtapp is None:
            return
        self.vtgui = self.vtapp.gui

        # Create the Plugins menu and insert it before the Help menu
        self.plugins_menu = QtGui.QMenu(translate('PluginsMenu', "&Plugins", 
            'The Plugins menu entry'))
        for menu in self.vtgui.menuBar().findChildren(QtGui.QMenu):
            if menu.objectName() == 'help_menu':
                self.vtgui.menuBar().insertMenu(menu.menuAction(), 
                    self.plugins_menu)

        # The Plugins menu cannot be populated without knowing which 
        # plugins are loaded so we have to wait until the convenience
        # pluginsLoaded signal is emitted
        self.vtapp.pluginsLoaded.connect(self.populateMenu)


    def populateMenu(self):
        """Populate the `Plugins` menu.
        """

        loaded_plugins = self.vtapp.plugins_mgr.loaded_plugins
        # Create a QAction for every loaded plugin
        for pgID in loaded_plugins.keys():
            pg_instance = loaded_plugins[pgID]
            if hasattr(pg_instance, 'helpAbout'):
                slot = self.showInfo
                name = pg_instance.helpAbout()['plugin_name']
            else:
                slot = self.noInfo
                name = pgID.split('#@#')[1]
            action = QtGui.QAction(name, self.plugins_menu, triggered=slot)
            action.setObjectName(pgID)
            self.plugins_menu.addAction(action)


    def helpAbout(self):
        """Brief description of the plugin."""

        # Text to be displayed
        about_text = translate('PluginsMenu', 
            """<qt>
            <p>This plugin inserts a <b>Plugins</b> menu in the 
            ViTables menu bar and adds an entry to it for each active 
            plugin. Selecting these menu entries will bring up a short 
            <b>About plugin</b> dialog with a brief description of the
            plugin.
            </qt>""",
            'Text of an About plugin message box')

        descr = dict(module_name='plugins_menu.py', 
            folder=os.path.join(PLUGINSDIR, 'menu'), 
            version=__version__, 
            plugin_name='Plugins menu', 
            author='Vicent Mas <vmas@vitables.org>', 
            descr=about_text)

        return descr


    def noInfo(self):
        """
        Message box with a 'No information available' message.

        This slot is called if an entry from the `Plugins` menu is activated
        but the referred plugin doesn't provide a `helpAbout` method.
        """

        # Text to be displayed
        about_text = translate('PluginsMenu', 
            "Sorry, there is not available information about this plugin.",
            'Text of the About Plugin message box')

        title = translate('PluginsMenu', 'About plugin', 
            'Title for an About plugin message box')

        QtGui.QMessageBox.about(self.vtgui, title, about_text)


    def showInfo(self):
        """Show a dialog with info about the active `Plugins` menu entry.

        This slot is called if an entry from the `Plugins` menu is activated.
        """

        action = self.sender()
        pgID = action.objectName()
        descr = self.vtapp.plugins_mgr.loaded_plugins[pgID].helpAbout()
        info_dlg = QtGui.QDialog(self.vtgui)
        info_dlg.setWindowTitle(
            translate('PluginsMenu', 'About plugin', 'A dialog title'))

        label1 = QtGui.QLabel(
            translate('PluginsMenu', 'Module name:', 'Label text'), info_dlg)
        label2 = QtGui.QLabel(
            translate('PluginsMenu', 'Folder:', 'Label text'), info_dlg)
        label3 = QtGui.QLabel(
            translate('PluginsMenu', 'Plugin name:', 'Label text'), info_dlg)
        label4 = QtGui.QLabel(
            translate('PluginsMenu', 'Version:', 'Label text'), info_dlg)
        label5 = QtGui.QLabel(
            translate('PluginsMenu', 'Author:', 'Label text'), info_dlg)
        label6 = QtGui.QLabel(
            translate('PluginsMenu', 'Description:', 'Label text'), info_dlg)

        palette = QtGui.QPalette(QtGui.qApp.palette())
        palette.setColor(QtGui.QPalette.Active, QtGui.QPalette.Base, 
            palette.window().color())
        field1 = setupTextWidget(info_dlg, palette)
        field1.setText(descr['module_name'])
        field2 = setupTextWidget(info_dlg, palette)
        field2.setText(descr['folder'])
        field3 = setupTextWidget(info_dlg, palette)
        field3.setText(descr['plugin_name'])
        field4 = setupTextWidget(info_dlg, palette)
        field4.setText(descr['version'])
        field5 = setupTextWidget(info_dlg, palette)
        field5.setText(descr['author'])
        field6 = setupTextWidget(info_dlg, palette, kind='text')
        field6.setText(descr['descr'])

        button_box = QtGui.QDialogButtonBox(info_dlg)
        button_box.addButton(QtGui.QDialogButtonBox.Ok)

        # Add a Configure button if the plugin description has a 'config' key
        try:
            if descr['config'] == True:
                config_button = button_box.addButton(\
                    translate('PluginsMenu', 'Configure...', 'Button text'), 
                    QtGui.QDialogButtonBox.ActionRole)
                pg_conf = self.vtapp.plugins_mgr.loaded_plugins[pgID].configure
                config_button.clicked.connect(pg_conf)
        except KeyError:
            pass

        grid = QtGui.QGridLayout(info_dlg)
        grid.addWidget(label1, 0, 0)
        grid.addWidget(field1, 0, 1)
        grid.addWidget(label2, 1, 0)
        grid.addWidget(field2, 1, 1)
        grid.addWidget(label3, 2, 0)
        grid.addWidget(field3, 2, 1)
        grid.addWidget(label4, 3, 0)
        grid.addWidget(field4, 3, 1)
        grid.addWidget(label5, 4, 0)
        grid.addWidget(field5, 4, 1)
        grid.addWidget(label6, 5, 0)
        grid.addWidget(field6, 5, 1)
        grid.addWidget(button_box, 6, 1)

        button_box.accepted.connect(info_dlg.close)
        info_dlg.show()




