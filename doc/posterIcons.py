# -*- coding: utf-8 -*-

#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

iconsDir = '/home/vmas/ViTables/hg_branches/vitables_tip/vitables/icons/'
big_icons = [('file_rw', 'The root node (read-write)'),
    ('file_ro', 'The root node (read-only)'),
    ('dbfilters', 'The root node of the Query Results file'),
    ('folder', 'A collapsed group '), 
    ('document-open-folder', 'An expanded group ')]
small_icons = [('table', 'A table (heterogeneus dataset) '),
    ('array', 'A regular array (homogeneus dataset) '),
    ('earray', 'An enlargeable array'),
    ('carray', 'A compressed array'),
    ('vlarray', 'A variable length array'),
    ('vlstring', 'An array of VLStrings'),
    ('object', 'A serialized objects dataset'),
    ('image-missing', 'An unsupported dataset')]

class Poster(QMainWindow) :
    def __init__(self, *args) :
        apply(QMainWindow.__init__, (self,) + args)
        w = QWidget(self)
        l = QGridLayout(w)
        self.setCentralWidget(w)
        self.makePoster()


    def changePalette(self, widget):
        palette = QPalette()
        self.palette().setColor(widget.backgroundRole(), Qt.white)
        widget.setPalette(palette)


    def makePoster(self):
        widget = self.centralWidget()
        layout = widget.layout()
        r = 0
        iconsDict = {'big_icons': big_icons, 'small_icons': small_icons}
        for key in iconsDict.keys():
            for (name, caption) in iconsDict[key] :
                pixmap = QPixmap()
                image_path = '%s/%s.png' % ("%s%s" % (iconsDir, key), name)
                print image_path
                pixmap.load(image_path)
                imLabel = QLabel(widget)
                imLabel.setPixmap(pixmap)
                self.changePalette(imLabel)
                layout.addWidget(imLabel, r, 0, 1, 1)
                textLabel = QLabel(caption,widget)
                self.changePalette(textLabel)
                layout.addWidget(textLabel, r, 1, 1, 1)
                r = r + 1


def main(args) :
    app = QApplication(args)
    poster = Poster()
    poster.show()
    app.exec_()

if __name__ == '__main__' :
    main(sys.argv)
