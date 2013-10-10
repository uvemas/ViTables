#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""Plugin that provides nice string formatting for time fields.

It supports not only native `PyTables` time datatypes but also the time
series contained in `PyTables` tables generated via ``scikits.timeseries``.
"""

__docformat__ = 'restructuredtext'
__version__ = '2.0'
plugin_class = 'TSFormatter'
plugin_name = 'Time series formatter'
comment = 'Display time series in a human friendly format'

import time
import os
import configparser

import tables

try:
    import scikits.timeseries as ts
except ImportError:
    ts = None

try:
    import pandas as pd
except ImportError:
    pd = None

from PyQt4 import QtCore
from PyQt4 import QtGui

import vitables.utils
from vitables.plugin_utils import getLogger
from vitables.plugins.timeseries.aboutpage import AboutPage
from vitables.vttables import leaf_model

translate = QtGui.QApplication.translate

LOGGER = getLogger()

def findPandasTS(leaf, attrs):
    ok = False
    time_cols = []
    if pd and isinstance(leaf, tables.Table) and hasattr(attrs, 'index_kind')\
    and (attrs.index_kind in ('datetime64', 'datetime32')):
        time_cols.append(leaf.coldescrs['index']._v_pos)
        ok = True
    return (ok, time_cols)


def formatPandasTS(content):
    """Format a given date in a user friendly way.

    The textual representation of the date index is converted to a
    Timestamp instance that can be easily formatted.

    :Parameter content: the content of the table cell being formatted
    """

    date = pd.Timestamp(int(content))
    try:
        ts_format = datetimeFormat()
        return date.strftime(ts_format)
    except (ValueError, TypeError):
        return content


def findScikitsTS(leaf, attrs):
    ok = False
    time_cols = []
    ts_freq = 6000
    if ts and isinstance(leaf, tables.Table) and hasattr(attrs, 'CLASS') and \
    (attrs.CLASS == 'TimeSeriesTable'):
        ok = True
        time_cols.append(leaf.coldescrs['_dates']._v_pos)
        special_attrs = getattr(attrs, 'special_attrs', {'freq': 6000})
        ts_freq = special_attrs['freq']
    return (ok, time_cols, ts_freq)


def findTablePyTablesTS(leaf):
    ok = False
    time_cols =  []
    # Check for PyTables timeseries
    if  isinstance(leaf, tables.Table):
        coltypes = leaf.coltypes
        for name in leaf.colnames:
            if (name in coltypes) and (coltypes[name] in
                                       ('time32', 'time64')):
                ok = True
                time_cols.append(leaf.coldescrs[name]._v_pos)
    return (ok, time_cols)
    

def findArrayPyTablesTS(leaf):
    ok = False
    time_cols = []
    if (not isinstance(leaf, tables.Table)) and \
    (not isinstance(leaf, tables.VLArray)) and (leaf.atom.shape == ()) \
    and (leaf.atom.type in ('time32', 'time64')) and (len(leaf.shape) < 3):
        ok = True
        time_cols = [-1]
    return (ok, time_cols)


def formatPyTablesTS(content):
    """
    Format a given date in a user friendly way.

    The textual representation of the date index is converted to a UTC
    time that can be easily formatted. This method is called when the
    timeseries has not been created using a third party library (i.e;
    Pandas, scikits.timeseries packages).
    """

    try:
        ts_format = datetimeFormat()
        return time.strftime(ts_format, time.gmtime(content))
    except (ValueError, TypeError):
        return content


def datetimeFormat():
    """The format string to be used when rendering the time series.
    """

    config = configparser.ConfigParser(interpolation=None)
    ini_filename = os.path.join(os.path.dirname(__file__), 'time_format.ini')
    def_dtformat = '%c'
    try:
        config.read_file(open(ini_filename))
        datetime_format = config['Timeseries']['strftime']
    except (IOError, configparser.ParsingError):
        datetime_format = def_dtformat

    return datetime_format


def customiseModel(datasheet):
    """Inspect a leaf model and customise it if a time series is found.

    When finding out if the datasheet contains time fields any found time
    field that cannot be formatted is skipped so:

        - time series created via ``pandas`` module are ignored if that
          module is not available
        - time series created via ``scikits.timeseries`` module are
          ignored if that module is not available
        - time fields that are displayed in a multidimensional cell
          are ignored

    The last restriction includes the following cases:

        - time fields that are part of a nested field
        - time fields in `VLArrays`
        - time fields in arrays with more than 2 dimensions
        - time fields in arrays with atom shape other than ()

    As far as the position of the time field being formatted is concerned the
    following cases can occur:

    - scikits_ts: leaf is a `TimeSeriesTable` instance. It contains just one
      time field, in a column labeled as `_dates`.
    - pandas_ts: leaf is a regular `tables.Table` instance with a column
      named `index`.
    - pytables_ts and leaf is a regular `tables.Table` instance. Every column
      can contain a time data type so we must inspect every column
    - pytables_ts and leaf is a `tables.Array` instance. As it is a homogeneous
      data container if a column contains a time data type then every column
      contains a time data type. Specific positions are not required.

    :Parameter datasheet: the :meth:`vitables.vttables.datasheet.DataSheet`
      instance being inspected
    """
    
    # Functions `table_data` and `array_data` will override the `data`
    # function of the leaf model when necessary. So this is MONKEY PATCHING.
    def table_data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.
    
        This is an overwritten method.
    
        :Parameters:
    
        - `index`: the index of a data item
        - `role`: the role being returned
        """
    
        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return None
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(),
            index.column())
        if role == QtCore.Qt.DisplayRole:
            if index.column() in time_cols:
                return time_formatter(cell)
            return self.formatContent(cell)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        else:
            return None


    def array_data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.
    
        This is an overwritten method.
    
        :Parameters:
    
        - `index`: the index of a data item
        - `role`: the role being returned
        """
    
        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return None
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(),
            index.column())
        if role == QtCore.Qt.DisplayRole:
            return time_formatter(cell)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        else:
            return None

    # If the node is a soft/external link then dereference it
    leaf = datasheet.dbt_leaf.node
    if isinstance(leaf, tables.link.Link):
        leaf = leaf.__call__()
    attrs = leaf._v_attrs

    node_kind = datasheet.dbt_leaf.node_kind

    (ok, time_cols) = findPandasTS(leaf, attrs)
    if ok:
        time_formatter = formatPandasTS
        datasheet.leaf_model.data = table_data
        return

    (ok, time_cols, ts_freq) = findScikitsTS(leaf, attrs)
    if ok:
        def formatScikitsTS(content):
            """Format a given date in a user friendly way.
        
            The textual representation of the date index is converted to a Date
            instance that can be easily formatted.
        
            :Parameter content: the content of the table cell being formatted
            """
        
            date = ts.Date(ts_freq, value=int(content))
            try:
                ts_format = datetimeFormat()
                return date.datetime.strftime(ts_format)
            except ValueError:
                return content

        # Only time series created via ``scikits.timeseries`` module have
        # freq attribute which defaults to 6000 meaning daily frequency
        time_formatter = formatScikitsTS
        leaf_model.LeafModel.data = table_data
        return

    (ok, time_cols) = findTablePyTablesTS(leaf) 
    if ok:
        time_formatter = formatPyTablesTS
        datasheet.leaf_model.data = table_data
        return
        
    (ok, time_cols) = findArrayPyTablesTS(leaf) 
    if ok:
        time_formatter = formatPyTablesTS
        leaf_model.LeafModel.data = array_data
        return


class TSFormatter(object):
    """Human friendly formatting of time series in a dataset.

    An inspector class intended for finding out if a `tables.Leaf` instance
    contains a time series suitable to be formatted in a user friendly way.
    """

    def __init__(self):
        """Class constructor.

        Dynamically finds new instances of
        :meth:`vitables.vttables.leaf_model.LeafModel` and customises them if
        they contain time fields.
        """

        self.vtapp = vitables.utils.getVTApp()
        self.vtapp.leaf_model_created.connect(customiseModel)


    def helpAbout(self, parent):
        """Full description of the plugin.

        This is a convenience method which works as expected by
        :meth:preferences.preferences.Preferences.aboutPluginPage i.e.
        build a page which contains the full description of the plugin
        and, optionally, allows for its configuration.

        :Parameter about_page: the container widget for the page
        """

        # Plugin full description
        desc = {'version': __version__,
            'module_name': os.path.join(os.path.basename(__file__)),
            'folder': os.path.join(os.path.dirname(__file__)),
            'author': 'Vicent Mas <vmas@vitables.org>',
            'about_text': translate('TimeFormatterPage',
            """<qt>
            <p>Plugin that provides nice string formatting for time fields.
            <p>It supports not only native PyTables time datatypes but
            also time series generated (and stored in PyTables tables) via
            Pandas and scikits.timeseries packages.
            </qt>""",
            'Text of an About plugin message box')}
        self.about_page = AboutPage(desc, parent)

        # We need to install the event filter because the Preferences dialog
        # eats all Return key presses even if the time format editor widget
        # has the keyboard focus (so connecting the returnPressed signal
        # of this widget to the AboutPage.applyFormat is useless)
        parent.parent().installEventFilter(self.about_page)
        return self.about_page
