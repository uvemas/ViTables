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
#       $Id: preferencesGUI.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the PreferencesGUI class.

Classes:

* PreferencesGUI(qt.QTabDialog)

Methods:

* __init__(self, name=None, modal=0, flags=0)
* __tr(self, source, comment=None)
* composeStartupGB(self, startup_gb)
* arrangeLoggerGB(self, logger_gb, layout)
* arrangeWorkspaceGB(self, workspace_gb)
* arrangeStyleGB(self, style_gb)

Functions:

* addToLayout(layout, *widgets_list)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import qt

def addToLayout(layout, *widgets_list):
    """Add a list of widgets to a given layout."""

    for widget in widgets_list:
        layout.addWidget(widget)


class PreferencesGUI(qt.QTabDialog):
    """
    Creates the `Preferences` dialog.

    The `Preferences` dialog is a tabbed dialog with 2 pages, ``General``
    and ``Look&Feel``.
    In the ``General`` page the startup behavior can be configured.
    In the ``Look&Feel`` page the configurable settings are:

    - font, foreground and background color of the logger
    - background color of the workspace
    - application style

    The dialog has ``OK``, ``Default``, ``Apply`` and ``Cancel``
    buttons. They behave as usual.
    """


    def __init__(self, name=None, modal=0, flags=0):
        """
        Init the preferences dialog and makes the GUI.

        :Parameters:

        - `name`: the name of the dialog (a string)
        - `modal`: TRUE if the dialog is modal (blocks the application)
        - `flags`: flags
        """

        qt.QTabDialog.__init__(self, qt.qApp.mainWidget(), name, modal, flags)
        self.setCaption(self.__tr('ViTables configuration dialog',
            'Caption of the preferences dialog'))

        # Make the General page
        general_page = qt.QWidget(self)
        general_layout = qt.QVBoxLayout(general_page)
        startup_gb = qt.QGroupBox(3, qt.Qt.Vertical, general_page)
        self.restore_cb = qt.QCheckBox(startup_gb)
        self.hiden_bg = qt.QButtonGroup()
        self.composeStartupGB(startup_gb)
        general_layout.addWidget(startup_gb)
        # Add page to dialog
        self.addTab(general_page, self.__tr('&General',
            'The title of the first dialog tab'))

        # Make the Look & Feel page
        lf_page = qt.QWidget(self)
        lf_layout = qt.QVBoxLayout(lf_page)
        logger_gb = qt.QGroupBox(2, qt.Qt.Horizontal, lf_page)
        buttons_parent = qt.QWidget(logger_gb)
        buttons_layout = qt.QVBoxLayout(buttons_parent)
        self.font_pb = qt.QPushButton(self.__tr('&Font',
            'The label of the logger font chooser button'),
            buttons_parent)
        self.foreground_pb = qt.QPushButton(self.__tr('F&oreground',
            'The label of the logger text color button'),
            buttons_parent)
        self.background_pb = qt.QPushButton(self.__tr('&Background',
            'The label of the logger color button'),
            buttons_parent)
        text = """<p>En un lugar de La Mancha,<br>""" \
        """de cuyo nombre no quiero acordarme,<br>""" \
        """no ha mucho tiempo vivia un hidalgo...</p>"""
        self.sample_te = qt.QTextEdit(logger_gb)
        self.sample_te.setText(text)
        self.arrangeLoggerGB(logger_gb, buttons_layout)
        workspace_gb = qt.QGroupBox(2, qt.Qt.Horizontal, lf_page)
        self.workspace_pb = qt.QPushButton(workspace_gb)
        self.workspace_label = qt.QLabel(workspace_gb)
        self.arrangeWorkspaceGB(workspace_gb)
        style_gb = qt.QGroupBox(3, qt.Qt.Horizontal, lf_page)
        self.styles_cb = qt.QComboBox(style_gb)
        self.arrangeStyleGB(style_gb)
        addToLayout(lf_layout, logger_gb, workspace_gb, style_gb)
        # Add page to dialog
        self.addTab(lf_page, self.__tr('&Look and Feel',
            'The title of the second dialog tab'))

        # Configure button's labels
        self.setApplyButton(self.__tr('Apply', 'Label of the Apply button'))
        self.setDefaultButton(self.__tr('Default',
            'Label of the Default button'))
        self.setCancelButton(self.__tr('Cancel', 'Label of the Cancel button'))


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('PreferencesGUI', source, comment).latin1()


    def composeStartupGB(self, startup_gb):
        """
        Add components to the Startup group box of the General page.

        :Parameter startup_gb: the groupbox being composed.
        """

        startup_gb.setTitle( self.__tr('Startup',
            'The name of the groupbox where startup is configured'))
        # An invisible button group is used to make radio buttons exclusive
        self.hiden_bg.setRadioButtonExclusive(1)

        #  Add Current directory entry to groupbox
        current_dir_rb = qt.QRadioButton(startup_gb)
        current_dir_rb.setText(self.__tr('Start in home directory',
            'Label of the startup in home directory radio button'))
        self.hiden_bg.insert(current_dir_rb, 1)

        #  Add Last opened directory entry to groupbox
        last_dir_rb = qt.QRadioButton(startup_gb)
        last_dir_rb.setText(self.__tr('Start in last opened directory',
            'Label of the startup in the last open directory radio button'))
        self.hiden_bg.insert(last_dir_rb, 2)

        #  Add Restore last session entry to groupbox
        self.restore_cb.setText(self.__tr('Restore last session',
            'Label of the restore last session check button'))


    def arrangeLoggerGB(self, logger_gb, layout):
        """
        Add the Logger group box to the Look & Feel page of Preferences.

        :Parameters:

        - `logger_gb`: the groupbox being arranged
        - `layout`: the layout for arranging buttons
        """

        logger_gb.setTitle(self.__tr('Logger',
            'The title of the logger groubox'))

        addToLayout(layout, self.font_pb, self.foreground_pb,
            self.background_pb)
        self.sample_te.setReadOnly(1)
        self.sample_te.setTextFormat(qt.Qt.RichText)


    def arrangeWorkspaceGB(self, workspace_gb):
        """
        Add the Workspace group box to the Look & Feel page of Preferences.

        :Parameter workspace_gb: the groupbox being arranged
        """

        workspace_gb.setTitle(self.__tr('Workspace',
            'The title of the workspace groupbox'))

        # Compose the Workspace group box
        self.workspace_pb.setText(self.__tr('Background',
            'The label of the workspace color button'))
        self.workspace_label.setText(self.__tr('Background color sample',
            'A label for the workspace color sample'))


    def arrangeStyleGB(self, style_gb):
        """
        Add the Style group box to the Look & Feel page of Preferences.

        :Parameter style_gb: the groupbox being arranged
        """

        style_gb.setTitle(self.__tr('Style',
            'The title of the global aspect groupbox'))

        # Style names can be retrieved with qt.QStyleFactory.keys()
        # The following map between qt.QStyles and style names applies:
        # 'qt.QWindowsStyle': 'Windows',
        # 'qt.QWindowsXPStyle': 'WindowsXP',
        # 'qt.QMotifStyle': 'Motif',
        # 'qt.QMotifPlusStyle': 'MotifPlus',
##            'qt.QMacStyle': 'Macintosh',
        # 'qt.QAquaStyle': 'Macintosh (Aqua)',
        # 'qt.QPlatinumStyle': 'Platinum',
        # 'qt.QSGIStyle': 'SGI',
        # 'qt.QCDEStyle': 'CDE'
        # WindowsXP and Macintosh (Aqua) styles are only implemented in
        # the PyQt for these platforms
        styles = ['default', 'Windows', 'Motif',  'MotifPlus', 'Platinum',
            'SGI', 'CDE']
        for item in styles:
            self.styles_cb.insertItem(item)
