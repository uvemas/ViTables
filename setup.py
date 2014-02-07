#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
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

"""
Setup script for the vitables package.
"""

from setuptools import setup, find_packages

setup(name='ViTables',
      version='2.1',
      description='A viewer for PyTables package',
      long_description=(
          'ViTables is a GUI for PyTables (a hierarchical database '
          'package designed to efficently manage very large amounts of '
          'data) . It allows to open arbitrarely large PyTables and HDF5 '
          'files and browse their data and metadata in a variety of ways.'),
      author='Vicent Mas',
      author_email='uvemas@gmail.com',
      maintainer='Vicent Mas',
      maintainer_email='uvemas@gmail.com',
      url='http://www.vitables.org',
      license='GPLv3, see the LICENSE.txt file for detailed info',
      platforms='Unix, MacOSX, Windows',
      classifiers=['Development Status :: 4 - Pre-Alpha',
                   'Environment :: X11 Applications',
                   'Environment :: MacOS X',
                   'Environment :: Win32 (MS Windows)',
                   'Operating System :: POSIX',
                   'Programming Language :: Python'],
      requires=['sip', 'PyQt4', 'numpy (>=1.4.1)', 'numexpr (>=2.0)',
                'cython (>=0.13)', 'tables (>=3.0)'],
      scripts=['scripts/vitables'],
      packages=find_packages(),
      include_package_data=True,)
