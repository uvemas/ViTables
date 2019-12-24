#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2019 Vicent Mas. All rights reserved
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


install_requires = ['qtpy (>=1.2.1)', 'numpy (>=1.4.1)', 'numexpr (>=2.0)',
                    'tables (>=3.0)']
if 'CONDA_PREFIX' not in os.environ:
    install_requires.append('PyQt5 (>=5.5.1)')

setup(name='ViTables',
      version=read('VERSION'),
      description='A viewer for PyTables package',
      long_description=read('README.txt'),
      author='Vicent Mas',
      author_email='vmas@vitables.org',
      maintainer='Vicent Mas',
      maintainer_email='vmas@vitables.org',
      url='https://vitables.org',
      license='GPLv3, see the LICENSE.txt file for detailed info',
      keywords='HDF5 PyTables',
      platforms='Unix, MacOSX, Windows',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: X11 Applications',
          'Environment :: MacOS X',
          'Environment :: Win32 (MS Windows)',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering'
      ],
      install_requires=install_requires,
      entry_points={
          'console_scripts': ['vitables = vitables.start:gui'],
          'vitables.plugins':
          [('columnar_org = '
            'vitables.plugins.columnorg.columnar_org:ArrayColsOrganizer'),
           ('dbs_tree_sort = '
            'vitables.plugins.dbstreesort.dbs_tree_sort:DBsTreeSort'),
           ('time_series = '
            'vitables.plugins.timeseries.time_series:TSFormatter')]
      },
      packages=find_packages(),
      # Include data files that belong to the vitables package
      package_data={
                'vitables': ['LICENSE.html',
                             'htmldocs/*', 'htmldocs/*/*',
                             'icons/*', 'icons/*/*',
                             '*/*.ui', 'plugins/*/*.ui',
                             'plugins/*/*.ini',
                             'i18n/*.qm'
                             ]
      },
      # In order to include files that do not belong to any package we have to
      # add them to MANIFEST.in AND set the include_package_data keyword to
      # True
      # include_package_data=True,
      )
