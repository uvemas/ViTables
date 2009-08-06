# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005, 2006, 2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008, 2009 Vicent Mas. All rights reserved
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

"""Plugin that provides basic support for the scikits.timeseries module.

In particular it allows for nicely formatting the time series contained
in PyTables tables generated via scikits.timeseries.
"""

__docformat__ = 'restructuredtext'
__version__ = '0.6'
plugin_class = 'TSFormatter'

import time

import tables

try:
    import scikits.timeseries as ts
except ImportError:
    ts = None

from PyQt4.QtCore import *

import vitables.utils

class TSFormatter(object):
    """An inspector class intended for finding out if a Leaf instance contains
    a time serie and formatting it in a user friendly way.
    """

    def __init__(self):
        """Class constructor.

        Dinamically finds new instances of LeafModel and customises them if
        a time serie is found in its dataset.
        """

        self.vtapp = vitables.utils.getVTApp()
        QObject.connect(self.vtapp, SIGNAL("leaf_model_created"), 
            self.customiseModel)


    def customiseModel(self, model):
        """Inspect a leaf model and customise it if a time serie is found.

        :Parameter model: the LeafModel instance being inspected
        """

        self.leaf = model.data_source
        self.ts_kind = self.findTS()
        self.ts_frequency = self.tsFrequency()
        model.time_cols = self.tsPositions()
        if model.time_cols != []:
            if model.time_cols == [-1]:
                # Dataset is an array of time series
                model.formatContent = self.timeFormatter()
                new_model= ArrayTSModel(model)
                model.data = new_model.data
            else:
                # Dataset is table with 1 or more time series
                model.formatTime = self.timeFormatter()
                new_model= TableTSModel(model)
                model.data = new_model.data


    def findTS(self):
        """Find out if the inspected leaf contains a time serie.
        """

        ts_kind = None
        if isinstance(self.leaf, tables.Table):
            # Leaf is a PyTables Table
            attrs = self.leaf._v_attrs
            if hasattr(attrs, 'CLASS') and attrs.CLASS == 'TimeSeriesTable':
                # The Table has been created via scikits.timeseries module
                ts_kind = 'scikits_ts'
            else:
                # The Table has been created in a standard way
                for cpath in self.leaf.colpathnames:
                    if self.leaf.coltypes[cpath] in ['time32', 'time64']:
                        ts_kind = 'pytables_ts'
                        break
        else:
            # Leaf is some kind of PyTables array
            atom_type = self.leaf.atom.type
            if atom_type in ['time32', 'time64']:
                ts_kind = 'pytables_ts'
        return ts_kind


    def tsFrequency(self):
        """Return the frequency (if any) of the time serie.

        Only time series created via scikits.timeseries module have
        this attribute.
        """

        ts_freq = None
        if self.ts_kind == 'scikits_ts':
            # The frequency of the time serie. Default is 6000 (daily)
            special_attrs = getattr(self.leaf._v_attrs, 'special_attrs', 
                {'freq': 6000})
            ts_freq = special_attrs['freq']
        return ts_freq


    def tsPositions(self):
        """Return the position of the time series going to be formatted.

        *If a time series cannot be formatted then it is ignored*.

        The following cases can occur:
        - leaf contains no time series that ViTables can format
        - leaf is a TimeSeriesTable instance. It contains just one time serie,
          in a column labeled as _dates. If scikits.timeseries module is not
          available this time serie cannot be formatted and will be ignored
        - leaf is a regular Table instance. Every column can contain a time
          serie so we must inspect every column
        - leaf is an Array instance. As it is a homogeneous data container if
          a column contains a time serie then every column contains a time
          serie. Specific positions are not required
        """

        positions = []
        if (self.ts_kind == 'scikits_ts') and ts:
            # If scikits.timeseries module is not available then ViTables
            # cannot format the time serie so it is ignored 
            positions.append(self.leaf.coldescrs['_dates']._v_pos)
        elif self.ts_kind == 'pytables_ts':
            if isinstance(self.leaf, tables.Table):
                for cpathname in self.leaf.colpathnames:
                    if self.leaf.coltypes[cpathname] in ['time32', 'time64']:
                        positions.append(self.leaf.coldescrs[cpathname]._v_pos)
            else:
                positions = [-1]
        return positions


    def timeFormatter(self, value=0):
        """Return the function to be used for formatting time series.
        """

        time_formatter = None
        if self.ts_kind == 'scikits_ts':
            time_formatter = self.formatScikitsTS
        elif self.ts_kind == 'pytables_ts':
            if isinstance(self.leaf, tables.Table):
                time_formatter = time.ctime
            else:
                time_formatter = vitables.utils.formatTimeContent
        return time_formatter


    def formatScikitsTS(self, value):
        """Format a given date in a user friendly way.

        Only Date instances (generated via scikits.timeseries module) are
        formatted with this method.

        :Parameter value: the value attribute for the Date object
        """

        date = ts.Date(self.ts_frequency, value=value)
        return date.datetime.strftime('%a %b %d %H:%M:%S %Y')


class ArrayTSModel(QAbstractTableModel):
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

        QAbstractTableModel.__init__(self, parent)
        self.numrows = model.numrows
        self.rbuffer = model.rbuffer
        self.formatContent = model.formatContent


    def data(self, index=QModelIndex(), role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return QVariant()
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), index.column())
        if role == Qt.DisplayRole:
            return QVariant(self.formatContent(cell))
        elif role == Qt.TextAlignmentRole:
            return QVariant(int(Qt.AlignLeft|Qt.AlignTop))
        else:
            return QVariant()


class TableTSModel(QAbstractTableModel):
    """
    A model for table datasets containing time series.

    The data is read from data sources (i.e., HDF5/PyTables nodes) by
    the model.
    """

    def __init__(self, model, parent=None):
        """Create the model.

        :Parameters:

            - `model`: the LeafModel instance being customised
            - `parent`: the parent of the model
        """

        QAbstractTableModel.__init__(self, parent)
        self.numrows = model.numrows
        self.rbuffer = model.rbuffer
        self.time_cols = model.time_cols
        self.formatTime = model.formatTime
        self.formatContent = model.formatContent


    def data(self, index=QModelIndex(), role=Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

        :Parameters:

        - `index`: the index of a data item
        - `role`: the role being returned
        """

        if not index.isValid() or \
            not (0 <= index.row() < self.numrows):
            return QVariant()
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), index.column())
        if role == Qt.DisplayRole:
            if index.column() in self.time_cols:
                return QVariant(self.formatTime(cell))
            return QVariant(self.formatContent(cell))
        elif role == Qt.TextAlignmentRole:
            return QVariant(int(Qt.AlignLeft|Qt.AlignTop))
        else:
            return QVariant()
