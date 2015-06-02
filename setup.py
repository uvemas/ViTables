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

import os
from setuptools import setup, find_packages


# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def find_package_datafiles(package):
    """
    Search a package for data files.

    Given a package, replace all occurrences of the '.' with '/' and
    search the directory for any file that is not a '.py' or '.pyc' file
    and add it to the list.  For each directory in the package, check to
    see if it is a package by checking for the '__init__.py' file.  If
    it is not a subpackage, recursively search it for more data files.

    """
    pkg_root = package.replace('.', '/')
    output = []
    fignores = ('.py', '.pyc')
    dignores = ('.git', '__pycache__')
    for filename in os.listdir(pkg_root):
        if filename in dignores:
            continue

        path = pkg_root + '/' + filename
        if os.path.islink(path):
            continue

        if os.path.isfile(path):
            if os.path.splitext(path)[1] not in fignores:
                output.append(filename)

        elif os.path.isdir(path):
            if os.path.exists(path + '/__init__.py'):
                # The subpackages are handled separately.
                continue

            for root, dirs, files in os.walk(path):
                print(root)
                for ignore in dignores:
                    if ignore in dirs:
                        dirs.remove(ignore)

                for dd in dirs:
                    if os.path.exists(dd + '/__init__.py'):
                        dirs.remove(dd)

                for ff in files:
                    if os.path.splitext(ff)[1] not in fignores:
                        # The path to the file is relative to the root
                        # of the package.  So, remove the package root.
                        fname = os.path.join(root, ff).replace('\\','/')
                        output.append(fname.replace(pkg_root + '/', ''))

    return output

setup(name='ViTables',
      version=read('VERSION'),
      description='A viewer for PyTables package',
      long_description=read('README.txt'),
      author='Vicent Mas',
      author_email='uvemas@gmail.com',
      maintainer='Alexey Naydenov',
      maintainer_email='alexey.naydenov@linux.com',
      url='http://www.vitables.org',
      license='GPLv3, see the LICENSE.txt file for detailed info',
      platforms='Unix, MacOSX, Windows',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: X11 Applications',
          'Environment :: MacOS X',
          'Environment :: Win32 (MS Windows)',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering'
      ],
      requires=['sip', 'PyQt4', 'numpy (>=1.4.1)', 'numexpr (>=2.0)',
                'cython (>=0.13)', 'tables (>=3.0)'],
      entry_points={
          'gui_scripts': ['vitables = vitables.start:gui'],
          'vitables.plugins':
          [('columnar_org = '
            'vitables.plugins.columnorg.columnar_org:ArrayColsOrganizer'),
           ('import_csv = '
            'vitables.plugins.csv.import_csv:ImportCSV'),
           ('export_csv = '
            'vitables.plugins.csv.export_csv:ExportToCSV'),
           ('dbs_tree_sort = '
            'vitables.plugins.dbstreesort.dbs_tree_sort:DBsTreeSort'),
           ('time_series = '
            'vitables.plugins.timeseries.time_series:TSFormatter')]
      },
      packages=find_packages(),
      include_package_data=True,
      package_data={
          pp : find_package_datafiles(pp) for pp in find_packages()
      },)
