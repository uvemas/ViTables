"""Default plugin about page."""

import os

from qtpy import QtGui
from qtpy import QtWidgets
from qtpy import uic

Ui_AboutPage = uic.loadUiType(os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'about_page.ui'))[0]


class AboutPage(QtWidgets.QWidget, Ui_AboutPage):
    def __init__(self, desc, parent=None):
        super(AboutPage, self).__init__(parent)
        self.setupUi(self)
        # fill gui elements
        self.version_text.setText(desc.get('version', ''))
        self.module_name_text.setText(desc.get('module_name', ''))
        self.folder_text.setText(desc.get('folder', ''))
        self.author_text.setText(desc.get('author', ''))
        self.desc_text.setText(desc.get('comment', ''))
