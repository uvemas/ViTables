"""Test class for start.py."""

import sys
import argparse

import pytest

from vitables import start, __version__


@pytest.mark.usefixtures('launcher')
class TestStart(object):
    def test_organizationDomain(self, launcher):
        start._set_credentials(launcher.app)
        organizationDomain = launcher.app.organizationDomain()
        assert organizationDomain == 'vitables.org'

    def test_organizationName(self, launcher):
        start._set_credentials(launcher.app)
        organizationName = launcher.app.organizationName()
        assert organizationName == 'ViTables'

    def test_applicationName(self, launcher):
        start._set_credentials(launcher.app)
        applicationName = launcher.app.applicationName()
        assert applicationName == 'ViTables'

    def test_applicationVersion(self, launcher):
        start._set_credentials(launcher.app)
        applicationVersion = launcher.app.applicationVersion()
        assert applicationVersion == __version__

    def test_l10n(self, launcher):
        # We must keep a reference to the translator or it will be destroyed
        # before the app quits
        translator = start._set_locale(launcher.app)
        assert launcher.app.translate('VTApp', 'Opening files...') == (
            'Abriendo ficheros...')

    def test_parseArgumentsCase1(self, launcher):
        sys.argv = ['vitables']
        args = start._parse_command_line()
        assert (args.mode, args.dblist, args.h5file) == ('a', '', [])

    def test_parseArgumentsCase2(self, launcher):
        sys.argv = ['vitables', '-m', 'r']
        args = start._parse_command_line()
        assert (args.mode, args.dblist, args.h5file) == ('r', '', [])

    def test_parseArgumentsCase3(self, launcher):
        sys.argv = ['vitables', '-m', 'c']
        try:
            start._parse_command_line()
        except (argparse.ArgumentError, SystemExit):
            assert True

    def test_parseArgumentsCase4(self, launcher):
        sys.argv = ['vitables', '-d']
        try:
            start._parse_command_line()
        except (argparse.ArgumentError, SystemExit):
            assert True

    def test_parseArgumentsCase5(self, launcher):
        sys.argv = ['vitables', '-d', 'tests/files_list.txt']
        args = start._parse_command_line()
        assert (args.mode, args.dblist, args.h5file) == ('', 'tests/files_list.txt', [])

    def test_parseArgumentsCase6(self, launcher):
        sys.argv = ['vitables', '-d', 'tests/files_list.txt', 'test.h5']
        args = start._parse_command_line()
        assert (args.mode, args.dblist, args.h5file) == ('', 'tests/files_list.txt', [])

    def test_parseArgumentsCase7(self, launcher):
        sys.argv = ['vitables', 'db1.h5', 'db2.h5']
        args = start._parse_command_line()
        assert (args.mode, args.dblist, args.h5file) == ('a', '',
                                                         ['db1.h5', 'db2.h5'])

    def test_loggerCase1(self, launcher):
        sys.argv = ['vitables', '-l', 'logfile.txt']
        args = start._parse_command_line()
        start._setup_logger(args)

    def test_loggerCase2(self, launcher):
        sys.argv = ['vitables', '-v']
        args = start._parse_command_line()
        start._setup_logger(args)

    def test_loggerCase3(self, launcher):
        sys.argv = ['vitables', '-v', '7']
        args = start._parse_command_line()
        start._setup_logger(args)

    def test_loggerCase4(self, launcher):
        sys.argv = ['vitables', '-v']
        args = start._parse_command_line()
        start._setup_logger(args)
