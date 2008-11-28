"""Run all test cases."""

import unittest
import sys
import os

import qt
import tables

def suite():
    """Make a suite that contains all test cases."""

    tests_modules = [
    'tests.h5db.test_dbManager', 
    'tests.h5db.test_dbDoc', 
    'tests.h5db.test_dbView', 
    'tests.nodes.test_arrayDoc', 
    'tests.nodes.test_groupDoc', 
    'tests.nodes.test_nodeDoc', 
    'tests.nodes.test_tableDoc', 
    'tests.nodes.test_unimplementedDoc', 
    'tests.root_package.test_actions', 
    'tests.root_package.test_commandLine', 
    'tests.root_package.test_query', 
    'tests.preferences.test_vtconfig', 
    'tests.preferences.test_preferences'
    ]
    all_tests = unittest.TestSuite()
    for name in tests_modules:
        exec('from %s import suite as test_suite' % name)
        all_tests.addTest(test_suite())
    return all_tests


def print_versions():
    """Print all the versions of software that ViTables relies on."""

    print '-=' * 38
    print 'ViTables version: %s' % vitables.preferences.vtconfig.getVersion()
    print "PyTables version:  %s" % tables.__version__
    print "Qt version:      %s" % qt.qVersion()
    print "PyQt version:      %s" % qt.PYQT_VERSION_STR
    print 'Python version:    %s' % sys.version
    if os.name == 'posix':
        (sysname, nodename, release, version, machine) = os.uname()
        print 'Platform:          %s-%s' % (sys.platform, machine)
    print '-=' * 38


if __name__ == '__main__':
    QAPP = qt.QApplication(sys.argv)
    import vitables.preferences.vtconfig
    print_versions()
    unittest.TextTestRunner().run(suite())
