# -*- coding: utf-8 -*-

#
# posterIcons.py
#
import sys, os

from qt import *

iconsDir = '/home/vmas/vitables/icons/'
big_icons = [('file_rw', 'The root node (read-write)'),
    ('file_ro', 'The root node (read-only)'),
    ('dbfilters', 'The root node of the Query Results file'),
    ('folder', 'A collapsed group '), 
    ('folder_open', 'An expanded group ')]
small_icons = [('table', 'A table (heterogeneus dataset) '),
    ('array', 'A regular array (homogeneus dataset) '),
    ('earray', 'An enlargeable array'),
    ('carray', 'A compressed array'),
    ('vlarray', 'A variable length array'),
    ('vlstring', 'An array of VLStrings'),
    ('object', 'A serialized objects dataset'),
    ('unimplemented', 'An unsupported dataset')]

class Poster(QMainWindow) :
    def __init__(self, *args) :
        apply(QMainWindow.__init__, (self,) + args)
        # intermediate container
        w = QWidget(self)
        l = QGridLayout(w, 13, 2, 6, 6)
        self.makePoster(w)
        self.setCentralWidget(w)
        w.setEraseColor(QColor(Qt.white))
        self.setEraseColor(QColor(Qt.white))


    def makePoster(self, widget) :
        layout = widget.layout()
        r = 0
        iconsDict = {'big_icons': big_icons, 'small_icons': small_icons}
        for key in iconsDict.keys():
            for icon in iconsDict[key] :
                pixmap = QPixmap()
                image = '%s/%s.png' % ("%s%s" % (iconsDir, key), icon[0])
                print image
                pixmap.load(image)
                text = icon[1]
                imLabel = QLabel(widget)
                imLabel.setPixmap(pixmap)
                imLabel.setEraseColor(QColor(Qt.white))
                layout.addWidget(imLabel, r, 0)
                textLabel = QLabel(text,widget)
                textLabel.setEraseColor(QColor(Qt.white))
                layout.addWidget(textLabel, r, 1)
                r = r + 1


def main(args) :
    app = QApplication(args)
    poster = Poster()
    app.setMainWidget(poster)
    poster.show()
    app.exec_loop()

if __name__ == '__main__' :
    main(sys.argv)
