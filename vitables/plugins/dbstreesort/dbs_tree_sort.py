#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2008-2013 Vicent Mas. All rights reserved
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

"""Plugin that provides sorting algorithms for the DBs tree.

At the moment only two sorting algorithms are supported, human (a.k.a.
natural sorting) and sorting by creation time.
"""

__docformat__ = 'restructuredtext'
__version__ = '1.0'
plugin_class = 'DBsTreeSort'
plugin_name = 'Tree of DBs sorting'
comment = 'Sorts the display of the databases tree'

import os

from PyQt4 import QtGui

import vitables
from vitables.plugins.dbstreesort.aboutpage import AboutPage

translate = QtGui.QApplication.translate

class DBsTreeSort(object):
    """
    """
    
    def __init__(self):
        """Class constructor.

        """

        self.vtapp = vitables.utils.getVTApp()


    def helpAbout(self, parent):
        """Full description of the plugin.

        This is a convenience method which works as expected by
        :meth:preferences.preferences.Preferences.aboutPluginPage i.e.
        build a page which contains the full description of the plugin
        and, optionally, allows for its configuration.

        :Parameter about_page: the container widget for the page
        """

        # Plugin full description
        desc = {'version': __version__,
            'module_name': os.path.join(os.path.basename(__file__)),
            'folder': os.path.join(os.path.dirname(__file__)),
            'author': 'Vicent Mas <vmas@vitables.org>',
            'about_text': translate('DBsTreeSortingPage',
            """<qt>
            <p>Plugin that provides sorting capabilities to the tree of DBs.
            <p>At the moment only two sorting algorithms are supported: human
            (a.k.a. natural sorting) and sorting by node creation time.
            </qt>""",
            'Text of an About plugin message box')}
        self.about_page = AboutPage(desc, parent)

        return self.about_page

