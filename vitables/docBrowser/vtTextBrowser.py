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
#       $Id: vtTextBrowser.py 1018 2008-03-28 11:31:46Z vmas $
#
########################################################################

"""
Here is defined the VTTextBrowser class and its helper classes.

Classes:

* VTTextBrowser(qt.QTextBrowser) 

Methods:

* __init__(self, parent) 
* __tr(self, source, comment=None)
* refreshSourceFactory(self, src_path)
* setSource(self, name)
* setSourceWin(self, name)
* setSourceWinNT(self, name)
* setSourceMacOSX(self, name)
* setSourceLinux(self, name)
* getLinuxBrowser(self)

Misc variables:

* __docformat__

"""
__docformat__ = 'restructuredtext'

import sys
import os
import subprocess

import qt

import vitables.utils

class VTTextBrowser(qt.QTextBrowser) :
    """A customized `QTextBrowser`."""


    def __init__(self, parent) :
        """
        Setup the widget that actually navigates docs.

        Rich text docs are displayed on a `QTextBrowser` in read-only mode.
        
        :Parameter parent:
            is an instance of the caller, i.e. an instance of
            `HelpBrowserGUI`
        """

        qt.QTextBrowser.__init__(self, parent)
        self.setTextFormat(qt.Qt.RichText)
        self.setReadOnly(1)
        self.msf = self.mimeSourceFactory()
        self.error_msg = self.__tr("""An error ocurred when atempting to """
                """start the web browser. The requested remote URL cannot """
                """be open.""",
                'A logger info message')

        # How to display external URLs depends on the platform
        if sys.platform.startswith('win'):
            # if VER_PLATFORM_WIN32_NT (i.e WindowsNT/2000/XP)
            if sys.getwindowsversion()[3] == 2:
                self.load_external_url = self.setSourceWinNT
            else:
                self.load_external_url = self.setSourceWin
        elif sys.platform.startswith('darwin'):
            self.load_external_url = self.setSourceMacOSX
        else:
            self.linux_browser = self.getLinuxBrowser()
            self.load_external_url = self.setSourceLinux


    def __tr(self, source, comment=None):
        """Translate method."""
        return qt.qApp.translate('VTTextBrowser', source, comment).latin1()

    
    def refreshSourceFactory(self, src_path):
        """
        If we change the user's guide directory (from the preferences
        dialog) when there are one or more documentation windows opened,
        the source path of the mime source factory must be updated.
        
        :Parameter src_path: is the search path for the mime source factory
        """
        self.msf.setFilePath(qt.QStringList(src_path))


    def setSource(self, name):
        """
        Set the name of the displayed document to name.

        QTextBrowser widgets can only navigate local documents. This
        method catches errors produced when we try to read remote docs.

        :Parameter name: the name of the document being displayed
        """

        if isinstance(name, qt.QString):
            name = name.latin1()

        # Internal URLs
        if not name.startswith('http://'):
            name = vitables.utils.forwardPath(os.path.abspath(name))
            qt.QTextBrowser.setSource(self, name)
        # External URLs
        else:
            self.load_external_url(name)


    def setSourceWin(self, name):
        """
        Display an external URL.

        This is a specialised handler for Windows platforms other than NT.

        :Parameter name: the name of the document being displayed
        """

        try:
            subprocess.Popen(['command.com', '/c', 'start', name])
        except OSError:
            print self.error_msg


    def setSourceWinNT(self, name):
        """
        Display an external URL.

        This is a specialised handler for Windows NT platforms, i.e.
        WinNT/2000/XP.

        :Parameter name: the name of the document being displayed
        """

        try:
            subprocess.Popen(['cmd.exe', '/c', 'start', name])
        except OSError:
            print self.error_msg


    def setSourceMacOSX(self, name):
        """
        Display an external URL.

        This is a specialised handler for Mac OS X platforms.

        :Parameter name: the name of the document being displayed
        """

        try:
            subprocess.Popen(['open', name])
        except OSError:
            print self.error_msg


    def setSourceLinux(self, name):
        """
        Display an external URL.

        This is a specialised handler for Linux platforms.

        :Parameter name: the name of the document being displayed
        """

        try:
            if self.linux_browser:
                subprocess.Popen([self.linux_browser, name])
        except OSError:
            print self.error_msg


    def getLinuxBrowser(self):
        """Get the graphical web browser to use on linux systems."""

        linux_browser = ''
        # Use $BROWSER if it exists
        if os.environ.has_key('BROWSER'):
            linux_browser = os.environ['BROWSER']
        # Use /etc/alternatives/x-www-browser if it exists
        elif os.path.isfile('/etc/alternatives/x-www-browser'):
            linux_browser = '/etc/alternatives/x-www-browser'
        # Look for the most typical browsers and uses the first it finds
        else:
            try:
                (out, err) = subprocess.Popen(['which', 'mozilla-firefox',
                    'konqueror','mozilla', 'netscape', 'opera', 'epiphany'],\
                    stdout=subprocess.PIPE).communicate()
                linux_browser = out.split('\n')[0]
            except OSError:
                print self.__tr("""No web browser can be found! Remote URLs """
                    """cannot be navigated.""",
                    'A logger info message')
        return linux_browser
