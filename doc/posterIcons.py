# -*- coding: utf-8 -*-

#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
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

#
# posterIcons.py
#
import sys

from qtpy import QtGui
from qtpy import QtWidgets

ICONSDIR = '../vitables/icons/'
big_icons = [('file_rw', 'The root node (read-write)'),
    ('file_ro', 'The root node (read-only)'),
    ('dbfilters', 'The root node of the Query Results file  '),
    ('folder', 'A collapsed group '), 
    ('document-open-folder', 'An expanded group ')]
small_icons = [('table', 'A table (heterogeneus dataset) '),
    ('array', 'A regular array (homogeneus dataset) '),
    ('earray', 'An enlargeable array'),
    ('carray', 'A compressed array'),
    ('vlarray', 'A variable length array'),
    ('vlstring', 'An array of VLStrings'),
    ('link_table', 'A soft link to a table (heterogeneus dataset) '),
    ('link_array', 'A soft link to a regular array (homogeneus dataset) '),
    ('link_earray', 'A soft link to an enlargeable array'),
    ('link_carray', 'A soft link to a compressed array'),
    ('link_vlarray', 'A soft link to a variable length array'),
    ('object', 'A serialized objects dataset'),
    ('image-missing', 'An unsupported dataset')]

class Poster(QtWidgets.QMainWindow) :
    def __init__(self) :
        super(QtWidgets.QMainWindow, self).__init__()
        w = QtWidgets.QWidget(self)
        l = QtWidgets.QGridLayout(w)
        self.setCentralWidget(w)
        self.makePoster()


    def makePoster(self):
        widget = self.centralWidget()
        layout = widget.layout()
        r = 0
        c = 0
        iconsDict = {'22x22': big_icons, '16x16': small_icons}
        for key in iconsDict.keys():
            for (name, caption) in iconsDict[key] :
                pixmap = QtGui.QPixmap()
                image_path = '{0}/{1}/{2}.png'.format(ICONSDIR, key, name)
                pixmap.load(image_path)
                imLabel = QtWidgets.QLabel(widget)
                imLabel.setPixmap(pixmap)
                layout.addWidget(imLabel, r, c, 1, 1)
                textLabel = QtWidgets.QLabel(caption,widget)
                layout.addWidget(textLabel, r, c + 1, 1, 1)
                r = r + 1
                if r > 8:
                    r = 0
                    c = 2


def main(args) :
    app = QtWidgets.QApplication(args)
    poster = Poster()
    poster.show()
    app.exec_()

if __name__ == '__main__' :
    main(sys.argv)
