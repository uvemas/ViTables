"""Test class for vtgui.py"""

import pytest
from qtpy import QtCore, QtGui, QtWidgets


@pytest.mark.usefixtures('launcher')
class TestLogger:
    @pytest.fixture()
    def logger(self, launcher):
        return launcher.gui.logger

    def test_write(self, logger):
        text_cursor = logger.textCursor()

        # Log regular message
        logger.clear()
        logger.write('Test text')
        assert logger.toPlainText() == 'Test text'

        # Log error message
        logger.clear()
        logger.write('\nError: test error text color')
        fmt = text_cursor.charFormat()
        color = fmt.foreground().color().name()
        assert color == '#ff0000'

        # Log warning message
        logger.clear()
        logger.write('\nWarning: test warning text color')
        fmt = text_cursor.charFormat()
        color = fmt.foreground().color().name()
        assert color == '#f38908'

    def test_setupContextMenu(self, launcher):
        cm = launcher.gui.findChild(QtWidgets.QMenu, 'logger_context_menu')
        menu_actions = cm.actions()
        assert cm

        actions = [a.objectName() for a in menu_actions
                   if not (a.isSeparator() or a.menu())]
        expected_actions = ['logger_copy_action', 'logger_clear_action',
                            'logger_select_action']
        assert sorted(actions) == sorted(expected_actions)

        separators = [a for a in menu_actions if a.isSeparator()]
        assert len(separators) == 1

    def test_updateContextMenu(self, logger):
        # Copy action enabled
        logger.clear()
        logger.write('Sample text')
        logger.selectAll()
        logger.updateContextMenu()
        assert logger.copy_action.isEnabled()

        # Copy action disabled
        text_cursor = logger.textCursor()
        text_cursor.clearSelection()
        # Update the visible cursor (see qtextedit.html#textCursor docs)
        logger.setTextCursor(text_cursor)
        logger.updateContextMenu()
        assert not logger.copy_action.isEnabled()

        # Clear/select action enabled
        logger.clear()
        logger.write('Sample text')
        logger.updateContextMenu()
        assert logger.clear_action.isEnabled()
        assert logger.select_action.isEnabled()

        # Clear/select action disabled
        logger.clear()
        logger.updateContextMenu()
        assert not logger.clear_action.isEnabled()
        assert not logger.select_action.isEnabled()

    def test_focusInEvent(self, launcher, logger):
        # Give keyboard focus to the logger
        # Notice that logger.setFocus() doesn't work if the widget is hidden
        launcher.app.sendEvent(logger, QtGui.QFocusEvent(QtCore.QEvent.FocusIn))
        # QTest.mouseClick(logger, QtCore.Qt.LeftButton)

        # Check the logger configuration
        assert logger.lineWidth() == 2
        assert logger.frameShape() == QtWidgets.QFrame.Panel
        assert logger.frameShadow() == QtWidgets.QFrame.Plain

    def test_focusOutEvent(self, logger, launcher):
        # Remove keyboard focus from the logger
        launcher.app.sendEvent(logger,
                               QtGui.QFocusEvent(QtCore.QEvent.FocusOut))

        # Check the logger configuration
        assert logger.lineWidth() == logger.frame_style['lwidth']
        assert logger.frameShape() == logger.frame_style['shape']
        assert logger.frameShadow() == logger.frame_style['shadow']
