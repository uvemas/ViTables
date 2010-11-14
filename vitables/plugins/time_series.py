# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2010 Vicent Mas. All rights reserved
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

It supports not only native PyTables time data types but also the time 
series contained in PyTables tables generated via scikits.timeseries.
"""

__docformat__ = 'restructuredtext'
_context = 'TSFormatter'
__version__ = '0.8'
plugin_class = 'TSFormatter'

import time

import tables

try:
    import scikits.timeseries as ts
except ImportError:
    ts = None

from PyQt4 import QtCore, QtGui

import vitables.utils
from vitables.vtSite import PLUGINSDIR


def trs(source, comment=None):
    """Translate string function."""
    return unicode(QtGui.qApp.translate(_context, source, comment))


def findTS(datasheet):
    """Find out if the inspected leaf contains a time field.

    **Existing time fields that cannot be formatted are skipped**:

        - time series created via scikits.timeseries module are
          ignored if that module is not available
        - time fields that are displayed in a multidimensional cell 
          are ignored

    The last restriction includes the following cases:

        - time fields that are part of a nested field
        - time fields in VLArrays
        - time fields in arrays with more than 2 dimensions
        - time fields in arrays with atom shape other than ()

    :Parameter `datasheet`: the DataSheet instance being inspected.
    :Return `ts_kind`: a flag indicating the kind of time series found
    """

    leaf = datasheet.dbt_leaf.node
    time_types = ['time32', 'time64']
    if isinstance(leaf, tables.Table):
        attrs = leaf._v_attrs
        coltypes = leaf.coltypes
        if hasattr(attrs, 'CLASS') and attrs.CLASS == 'TimeSeriesTable' \
            and ts:
            return 'scikits_ts'
        for name in leaf.colnames:
            if coltypes.has_key(name) and coltypes[name] in time_types: 
                return 'pytables_ts'
    elif leaf.atom.type in time_types and \
        len(leaf.shape) < 3 and \
        leaf.atom.shape == () and \
        datasheet.dbt_leaf.node_kind != u'vlarray': 
        return 'pytables_ts'
    else:
        return None


def tsPositions(ts_kind, leaf):
    """Return the position of the time field going to be formatted.

    The following cases can occur:
    - leaf is a TimeSeriesTable instance. It contains just one time field,
      in a column labeled as _dates.
    - leaf is a regular Table instance. Every column can contain a time
      data type so we must inspect every column
    - leaf is an Array instance. As it is a homogeneous data container if
      a column contains a time data type then every column contains a time
      data type. Specific positions are not required
    """

    positions = []
    if (ts_kind == 'scikits_ts'):
        positions.append(leaf.coldescrs['_dates']._v_pos)
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

    Only time series created via scikits.timeseries module have
    this attribute.
    """

    ts_freq = None
    if ts_kind == 'scikits_ts':
        # The frequency of the time serie. Default is 6000 (daily)
        special_attrs = getattr(leaf._v_attrs, 'special_attrs', 
            {'freq': 6000})
        ts_freq = special_attrs['freq']
    return ts_freq


class TSFormatter(object):
    """An inspector class intended for finding out if a Leaf instance contains
    a time series suitable to be formatted in a user friendly way.
    """

    def __init__(self):
        """Class constructor.

        Dinamically finds new instances of LeafModel and customises them if
        they contain time fields.
        """

        self.vtapp = vitables.utils.getVTApp()
        self.vtapp.leaf_model_created.connect(self.customiseModel)


    def customiseModel(self, datasheet):
        """Inspect a leaf model and customise it if a time field is found.

        :Parameter subwindow: the DataSheet instance being inspected
        """

        # Look for formattable time fields in the dataset
        ts_kind = findTS(datasheet)
        if ts_kind is None:
            return

        # Get the positions of the time fields
        leaf = datasheet.dbt_leaf.node
        time_cols = tsPositions(ts_kind, leaf)
        if time_cols == []:
            return

        model = datasheet.widget().model()
        if time_cols == [-1]:
            # Dataset is an array of time series
            new_model = ArrayTSModel(model)
            model.formatTimeContent = new_model.formatTimeContent
            model.data = new_model.data
        else:
            # Dataset is table with 1 or more time series
            freq = tsFrequency(ts_kind, leaf)
            model.time_cols = time_cols
            new_model = TableTSModel(model, freq, ts_kind)
            model.formatTime = new_model.formatTime
            model.data = new_model.data


    def helpAbout(self):
        """Brief description of the plugin."""

        # Text to be displayed
        about_text = trs(
            """<qt>
            <p>Plugin that provides nice string formatting for time fields.
            <p>It supports not only native PyTables time datatypes but 
            also the time series tables generated 
            via scikits.timeseries package.
            </qt>""",
            'Text of an About plugin message box')

        descr = dict(module_name='time_series.py', folder=PLUGINSDIR, 
            version=__version__, 
            plugin_name='Time series formatter', 
            author='Vicent Mas <vmas@vitables.org>', 
            descr=about_text)

        return descr


class ArrayTSModel(QtCore.QAbstractTableModel):
    """
    A model for array datasets containing time series.

    The data is read from data sources (i.e., HDF5/PyTables nodes) by
    the model.
    """

    def __init__(self, model, parent=None):
        """Create the model.

        :Parameters:

            - `model`: the LeafModel instance being customised
            - `parent`: the parent of the model
        """

        QtCore.QAbstractTableModel.__init__(self, parent)
        self.numrows = model.numrows
        self.rbuffer = model.rbuffer


    def formatTimeContent(self, content):
        """
        Nicely format the contents of a table widget cell using UTC times.

        Used when the content atom is TimeAtom.
        """
        return time.asctime(time.gmtime(content))


    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return QtCore.QVariant()
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), 
            index.column())
        if role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.formatTimeContent(cell))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.QVariant(int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop))
        else:
            return QtCore.QVariant()


class TableTSModel(QtCore.QAbstractTableModel):
    """
    A model for table datasets containing time series.

    The data is read from data sources (i.e., HDF5/PyTables nodes) by
    the model.
    """

    def __init__(self, model, freq, ts_kind, parent=None):
        """Create the model.

        :Parameters:

            - `model`: the LeafModel instance being customised
            - `freq`: the stime series frequency (if any)
            - `ts_kind`: the kind of time series
            - `parent`: the parent of the model
        """

        QtCore.QAbstractTableModel.__init__(self, parent)
        self.numrows = model.numrows
        self.rbuffer = model.rbuffer
        self.time_cols = model.time_cols
        self.freq = freq
        self.formatTime = self.timeFormatter(ts_kind)


    def timeFormatter(self, ts_kind):
        """Return the function to be used for formatting time series.
        """

        time_formatter = None
        if ts_kind == 'scikits_ts':
            time_formatter = self.formatScikitsTS
        elif ts_kind == 'pytables_ts':
            time_formatter = self.formatTimeContent
        return time_formatter


    def formatTimeContent(self, content):
        """
        Nicely format the contents of a table widget cell using UTC times.

        Used when the content atom is TimeAtom.
        """
        return time.asctime(time.gmtime(content))


    def formatScikitsTS(self, value):
        """Format a given date in a user friendly way.

        Only Date instances (generated via scikits.timeseries module) are
        formatted with this method.

        :Parameter value: the content of the table cell being formatted
        """

        date = ts.Date(self.freq, value=int(value))
        try:
            return date.datetime.strftime('%a %b %d %H:%M:%S %Y')
        except ValueError:
            return value


    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return QtCore.QVariant()
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), 
            index.column())
        if role == QtCore.Qt.DisplayRole:
            if index.column() in self.time_cols:
                return QtCore.QVariant(self.formatTime(cell))
            return QtCore.QVariant(vitables.utils.formatArrayContent(cell))
        elif role == QtCore.Qt.TextAlignmentRole:
            return QtCore.QVariant(int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop))
        else:
            return QtCore.QVariant()
