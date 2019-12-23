#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""Plugin that provides nice string formatting for time fields.

It supports not only native `PyTables` time datatypes but also the time
series contained in `PyTables` tables generated via ``scikits.timeseries`` and
``Pandas``.
"""

import time
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import tables

try:
    import scikits.timeseries as ts
except ImportError:
    ts = None

try:
    import pandas as pd
except ImportError:
    pd = None

from qtpy import QtCore, QtGui
from qtpy.QtCore import Qt
from qtpy import QtWidgets

import vitables.utils
from vitables.plugins.timeseries.aboutpage import AboutPage

_axis_font = QtGui.QFont()
_axis_font.setBold(True)

__docformat__ = 'restructuredtext'
__version__ = '2.1'
plugin_name = 'Time series formatter'
comment = 'Display time series in a human friendly format'

translate = QtWidgets.QApplication.translate


def findTS(leaf, node_kind):
    """Find out if the inspected leaf contains a time field.

    **Existing time fields that cannot be formatted are skipped**:

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

    :Parameters:
        - `leaf`: the tables.Leaf instance being inspected.
        - `node_kind`: a LeafNode attribute that indicates the kind of dataset

    :Return ts_kind: a flag indicating the kind of time series found
    """

    time_types = ['time32', 'time64']
    if isinstance(leaf, tables.Table):
        asi = leaf._v_attrs
        coltypes = leaf.coltypes
        pgroup = leaf._g_getparent()

        # Check for Pandas timeseries
        pandas_attr = getattr(pgroup._v_attrs, 'pandas_type', None)
        if pd and pandas_attr in ['frame', 'frame_table']:
            userattrs_names = asi._v_attrnamesuser
            dtype_attrs = [n for n in userattrs_names if n.endswith('_dtype')]
            dtype_attrs.append('index_kind')
            for n in dtype_attrs:
                if getattr(asi, n).startswith('datetime'):
                    return 'pandas_ts'

        # Check for scikits.timeseries timeseries
        if ts and hasattr(asi, 'CLASS') and (asi.CLASS == 'TimeSeriesTable'):
            return 'scikits_ts'

        # Check for PyTables timeseries
        for name in leaf.colnames:
            if (name in coltypes) and (coltypes[name] in time_types):
                return 'pytables_ts'
    elif (leaf.atom.type in time_types) and \
            (len(leaf.shape) < 3) and \
            (leaf.atom.shape == ()) and \
            (node_kind != 'vlarray'):
        return 'pytables_ts'

    return None


def tsPositions(ts_kind, leaf):
    """Return the position of the time field going to be formatted.

    The following cases can occur:

    - scikits_ts: leaf is a `TimeSeriesTable` instance. It contains just one
      time field, in a column labeled as `_dates`.
    - pandas_ts: leaf is a regular `tables.Table` instance with a column
      named `index`.
    - pytables_ts and leaf is a regular `tables.Table` instance. Every column
      can contain a time data type so we must inspect every column
    - pytables_ts and leaf is a `tables.Array` instance. As it is a homogeneous
      data container if a column contains a time data type then every column
      contains a time data type. Specific positions are not required.
    """

    positions = []
    if (ts_kind == 'scikits_ts'):
        positions.append(leaf.coldescrs['_dates']._v_pos)
    elif (ts_kind == 'pandas_ts'):
        hstore = pd.HDFStore(leaf._v_file.filename)
        pgroup = leaf._g_getparent()
        df = hstore[pgroup._v_name]

        # Inspect dataframe index
        df_index = df.index
        if isinstance(df_index, pd.MultiIndex):
            nlevels = df_index.nlevels
            for i, idx in enumerate(df_index.names):
                dtime = 'datetime'
                if df_index.get_level_values(i).dtype.name.startswith(dtime):
                    positions.append(i)
        elif df_index.dtype.name.startswith('datetime'):
            nlevels = 1
            positions.append(0)

        # Inspect dataframe data
        for i, dt in enumerate(df.dtypes):
            if dt.name.startswith('datetime'):
                positions.append(nlevels + i)
    elif ts_kind == 'pytables_ts':
        if isinstance(leaf, tables.Table):
            for name in leaf.colnames:
                if leaf.coltypes[name] in ['time32', 'time64']:
                    positions.append(leaf.coldescrs[name]._v_pos)
        else:
            positions = [-1]
    return positions


def tsFrequency(ts_kind, leaf):
    """Return the frequency (if any) of the time series.

    Only time series created via ``scikits.timeseries`` module have
    this attribute.
    """

    ts_freq = None
    if ts_kind == 'scikits_ts':
        # The frequency of the time serie. Default is 6000 (daily)
        special_attrs = getattr(leaf._v_attrs, 'special_attrs',
                                {'freq': 6000})
        ts_freq = special_attrs['freq']
    return ts_freq


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


class TSFormatter(object):
    """Human friendly formatting of time series in a dataset.

    An inspector class intended for finding out if a `tables.Leaf` instance
    contains a time series suitable to be formatted in a user friendly way.
    """

    UID = __name__
    NAME = plugin_name
    COMMENT = comment

    def __init__(self):
        """Class constructor.

        Dynamically finds new instances of
        :meth:`vitables.vttables.leaf_model.LeafModel` and customises them if
        they contain time fields.
        """

        self.vtapp = vitables.utils.getVTApp()
        self.vtapp.leaf_model_created.connect(self.customiseModel)

    def customiseModel(self, datasheet):
        """Inspect a leaf model and customise it if a time series is found.

        :Parameter subwindow: the :meth:`vitables.vttables.datasheet.DataSheet`
          instance being inspected
        """

        # If the node is a soft/external link then dereference it
        leaf = datasheet.dbt_leaf.node
        if isinstance(leaf, tables.link.Link):
            leaf = leaf.__call__()

        # Look for formattable time fields in the dataset
        node_kind = datasheet.dbt_leaf.node_kind
        ts_kind = findTS(leaf, node_kind)
        if ts_kind is None:
            return

        # Get the positions of the time fields
        time_cols = tsPositions(ts_kind, leaf)
        if time_cols == []:
            return

        # Customise the leaf model
        model = datasheet.widget().model()
        ts_info = {
            'ts_kind': ts_kind,
            'ts_cols': time_cols,
            'ts_freq': tsFrequency(ts_kind, leaf),
            'ts_format': datetimeFormat(),
        }
        if isinstance(leaf, tables.Table):
            if isinstance(model, vitables.vttables.df_model.DataFrameModel):
                leaf_kind = 'dataframe'
            else:
                leaf_kind = 'table'
        else:
            leaf_kind = 'array'
        model_info = {
            'leaf_kind': leaf_kind,
            'model': model,
            'numrows': model.rowCount(),
        }
        if leaf_kind in ['table', 'array']:
            model_info['formatContent'] = model.formatContent

        # Add required attributes to model
        for k in ts_info:
            setattr(model, k, ts_info[k])

        # Add/customise required methods to model
        ts_model = TSLeafModel(model_info, ts_info)
        model.tsFormatter = ts_model.tsFormatter
        model.data = ts_model.data

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


class TSLeafModel(object):
    """Provides a `data()` method to leaf models that contains time series.

    Formatting a table is more difficult than formatting an array because
    tables content is not homogeneous and columns with time series have to
    be formatted in a different way to the rest of columns.
    """

    def __init__(self, model_info, ts_info, parent=None):
        """The constructor method.

        All required attributes are set in this method.
        """

        # Attributes required by the tsFormatter() method
        self.ts_kind = ts_info['ts_kind']
        self.ts_freq = ts_info['ts_freq']
        self.ts_format = ts_info['ts_format']
        # Attributes required by the data() method
        self.model = model_info['model']
        self.numrows = model_info['numrows']
        self.ts_cols = ts_info['ts_cols']
        if 'formatContent' in model_info:
            self.formatContent = model_info['formatContent']

        self.tsFormatter = self.timeFormatter()

        leaf_kind = model_info['leaf_kind']
        if leaf_kind == 'table':
            self.data = self.table_data
        elif leaf_kind == 'dataframe':
            self.data = self.df_data
        else:
            self.data = self.array_data

    def table_data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        This is an overwritten method.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """
        row, col = index.row(), index.column()

        if not index.isValid() or not (0 <= row < self.numrows):
            return None

        if role == QtCore.Qt.DisplayRole:
            cell = self.model.cell(row, col)
            if index.column() in self.ts_cols:
                return self.tsFormatter(cell)
            return self.formatContent(cell)

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop

        return None

    def df_data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        This is an overwritten method.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """
        row, col = index.row(), index.column()
        n_columns, n_index = self.model._nheaders
        df = self.model._chunk

        if not index.isValid() or not (0 <= row < (self.numrows + n_columns)):
            return None

        is_index = col < n_index
        is_columns = (self.model.start + row) < n_columns

        if is_index and is_columns:
            return None

        if is_index:
            if role == Qt.DisplayRole:
                val = df.index[row - n_columns]
                if n_index > 1:
                    val = val[col]
                if col in self.ts_cols:
                    return self.tsFormatter(val)
                return str(val)
            if role == Qt.FontRole:
                return _axis_font
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return

        if is_columns:
            if role == Qt.DisplayRole:
                val = df.columns[col - n_index]
                if n_columns > 1:
                    val = val[row]
                return str(val)
            if role == Qt.FontRole:
                return _axis_font
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignCenter | Qt.AlignBottom)
            return

        if role == Qt.DisplayRole:
            val = self.model._chunk.iat[row - n_columns, col - n_index]
            if col in self.ts_cols:
                return self.tsFormatter(val)
            return str(val)

        # if role == Qt.TextAlignmentRole:
        #     return int(Qt.AlignLeft|Qt.AlignTop)

        return

    def array_data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        This is an overwritten method.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """
        row, col = index.row(), index.column()

        if not index.isValid() or not (0 <= row < self.numrows):
            return None

        if role == QtCore.Qt.DisplayRole:
            cell = self.model.cell(row, col)
            return self.tsFormatter(cell)

        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop

        return None

    def timeFormatter(self):
        """Return the function to be used for formatting time series.
        """

        time_formatter = None
        ts_kind = self.ts_kind
        if ts_kind == 'pandas_ts':
            time_formatter = self.formatPandasTS
        elif ts_kind == 'scikits_ts':
            time_formatter = self.formatScikitsTS
        elif ts_kind == 'pytables_ts':
            time_formatter = self.formatPyTablesTS
        return time_formatter

    def formatPyTablesTS(self, content):
        """
        Format a given date in a user friendly way.

        The textual representation of the date index is converted to a UTC
        time that can be easily formatted. This method is called when the
        timeseries has not been created using a third party library (i.e;
        Pandas, scikits.timeseries packages).
        """

        try:
            return time.strftime(self.ts_format, time.gmtime(content))
        except ValueError:
            return content

    def formatPandasTS(self, content):
        """Format a given date in a user friendly way.

        The textual representation of the date index is converted to a
        Timestamp instance that can be easily formatted.

        :Parameter content: the content of the table cell being formatted
        """
        try:
            return content.strftime(self.ts_format)
        except ValueError:
            return content

    def formatScikitsTS(self, content):
        """Format a given date in a user friendly way.

        The textual representation of the date index is converted to a Date
        instance that can be easily formatted.

        :Parameter content: the content of the table cell being formatted
        """

        date = ts.Date(self.ts_freq, value=int(content))
        try:
            return date.datetime.strftime(self.ts_format)
        except ValueError:
            return content
