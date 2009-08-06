# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2009 Dmitrijs Ledkovs. All rights reserved
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

import os.path
from PyQt4.uic import loadUiType

Ui_NodePropDialog = \
    loadUiType(os.path.join(os.path.dirname(__file__),'prop_dlg.ui'))[0]
