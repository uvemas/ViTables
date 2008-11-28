"""
Utilities for ViTables' test suites
===================================

:Author:   Vicent Mas, aka V+
:Contact:  vmas@carabos.com
:Created:  2006-07-11
:License:  ViTables commercial
:Revision: $Id: common.py 1495 2006-03-13 09:37:24Z faltet $
"""

import unittest
import tempfile
import os
import os.path
import warnings
import sys
import popen2
import time


verbose = False
"""Show detailed output of the testing process."""

if 'verbose' in sys.argv:
    verbose = True
    sys.argv.remove('verbose')


def verbosePrint(string):
    """Print out the `string` if verbose output is enabled."""
    if verbose: print string


def cleanup(klass):
    #klass.__dict__.clear()     # This is too hard. Don't do that
#    print "Class attributes deleted"
    for key in klass.__dict__.keys():
        if not klass.__dict__[key].__class__.__name__ in ('instancemethod'):
            klass.__dict__[key] = None


class PyTablesTestCase(unittest.TestCase):

    """Abstract test case with useful methods."""

    def _getName(self):
        """Get the name of this test case."""
        return self.id().split('.')[-2]


    def _getMethodName(self):
        """Get the name of the method currently running in the test case."""
        return self.id().split('.')[-1]


    def _verboseHeader(self):
        """Print a nice header for the current test method if verbose."""

        if verbose:
            name = self._getName()
            methodName = self._getMethodName()

            title = "Running %s.%s" % (name, methodName)
            print '%s\n%s\n' % (title, '-'*len(title))


