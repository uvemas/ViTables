# -*- coding: utf-8 -*-
#!/usr/bin/env python

#       Copyright (C) 2005-2007 Carabos Coop. V. All rights reserved
#       Copyright (C) 2008-2011 Vicent Mas. All rights reserved
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
__version__ = '0.9'
plugin_class = 'TSFormatter'

import time
import os
import ConfigParser

import tables

try:
    import scikits.timeseries as ts
except ImportError:
    ts = None

from PyQt4 import QtCore
from PyQt4 import QtGui


import vitables.utils
from vitables.vtSite import PLUGINSDIR
from vitables.plugins.timeseries.timeFormatterDlg import TimeFormatterDlg

translate = QtGui.QApplication.translate


def findTS(datasheet):
    """Find out if the inspected leaf contains a time field.

    **Existing time fields that cannot be formatted are skipped**:

        - time series created via ``scikits.timeseries`` module are
          ignored if that module is not available
        - time fields that are displayed in a multidimensional cell 
          are ignored

    The last restriction includes the following cases:

        - time fields that are part of a nested field
        - time fields in `VLArrays`
        - time fields in arrays with more than 2 dimensions
        - time fields in arrays with atom shape other than ()

    :Parameter datasheet: the :meth:`vitables.vtTables.dataSheet.DataSheet`
      instance being inspected.
    :Return ts_kind: a flag indicating the kind of time series found
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
            if name in coltypes and coltypes[name] in time_types: 
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

    - leaf is a `TimeSeriesTable` instance. It contains just one time field,
      in a column labeled as _dates.
    - leaf is a regular `tables.Table` instance. Every column can contain a
      time data type so we must inspect every column
    - leaf is an `tables.Array` instance. As it is a homogeneous data container
      if a column contains a time data type then every column contains a time
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


class TSFormatter(object):
    """Look for suitable time series in a dataset.

    An inspector class intended for finding out if a `tables.Leaf` instance contains
    a time series suitable to be formatted in a user friendly way.
    """

    def __init__(self):
        """Class constructor.

        Dinamically finds new instances of 
        :meth:`vitables.vtTables.leafModel.LeafModel` and customises them if
        they contain time fields.
        """

        self.vtapp = vitables.utils.getVTApp()
        self.vtapp.leaf_model_created.connect(self.customiseModel)


    def customiseModel(self, datasheet):
        """Inspect a leaf model and customise it if a time field is found.

        :Parameter subwindow: the :meth:`vitables.vtTables.dataSheet.DataSheet`
          instance being inspected
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
        """Brief description of the plugin.

        This is a convenience method which works as expected by
        :meth:menu.plugins_menu.showInfo i.e. it returns a dictionary
        whose keys will be used by the `menu` plugin in order to show
        information about this plugin.
        """

        # Text to be displayed
        about_text = translate('TSFormatter', 
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
            descr=about_text, 
            config=True)

        return descr


    def configure(self):
        """Configure the format used in a timeseries.

        This is a convenience method. If the `menu` plugin is enabled
        and its Time Series entry is activated then the raised dialog
        has a Configure button which is connected to this method.

        The timeseries format can be configured without calling this
        method simply by editing the time_format.ini file by hand.
        """
        TimeFormatterDlg()





class ArrayTSModel(QtCore.QAbstractTableModel):
    """
    A model (in the `MVC` sense) for array datasets containing time series.

    The data is read from data sources (i.e., `HDF5/PyTables` nodes) by
    the model.
    """

    def __init__(self, model, parent=None):
        """Create the model.

        :Parameters:

            - `model`: the LeafModel instance being customised
            - `parent`: the parent of the model
        """

        self.numrows = model.numrows
        self.numcols = model.numcols
        self.rbuffer = model.rbuffer

        super(ArrayTSModel, self).__init__(parent)

        config = ConfigParser.RawConfigParser()
        def_tformat = '%c' 
        try:
            config.read(\
                os.path.join(os.path.dirname(__file__), u'time_format.ini'))
            self.tformat = config.get('Timeseries', 'strftime')
        except (IOError, ConfigParser.Error):
            self.tformat = def_tformat



    def formatTimeContent(self, content):
        """
        Nicely format the contents of a table widget cell using UTC times.

        Used when the content atom is `TimeAtom`.
        """

        try:
            return time.strftime(self.tformat, time.gmtime(content))
        except ValueError:
            return content


    def data(self, index=QtCore.QModelIndex(), role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item
        referred to by the index.

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
            return self.formatTimeContent(cell)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        else:
            return None


    def rowCount(self, index):
        """The number of rows under the given index.

        When implementing a table based model this method has to be overriden
        -because it is an abstract method- and should return 0 for valid
        indices (because they have no children). If the index is not valid the 
        method  should return the number of rows exposed by the model.

        :Parameter index: the model index being inspected.
        """

        if not index.isValid():
            return self.numrows
        else:
            return 0


    def columnCount(self, index):
        """The number of columns for the children of the given index.

        When implementing a table based model this method has to be overriden
        -because it is an abstract method- and should return 0 for valid
        indices (because they have no children). If the index is not valid the 
        method  should return the number of columns exposed by the model.

        :Parameter index: the model index being inspected.
        """

        if not index.isValid():
            return self.numcols
        else:
            return 0


class TableTSModel(QtCore.QAbstractTableModel):
    """
    A model (in the `MVC` sense) for table datasets containing time series.

    The data is read from data sources (i.e., `HDF5/PyTables` nodes) by
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

        self.numrows = model.numrows
        self.numcols = model.numcols
        self.rbuffer = model.rbuffer
        self.time_cols = model.time_cols
        self.freq = freq
        self.formatTime = self.timeFormatter(ts_kind)

        super(TableTSModel, self).__init__(parent)

        config = ConfigParser.RawConfigParser()
        def_tformat = '%c' 
        try:
            config.read(\
                os.path.join(os.path.dirname(__file__), u'time_format.ini'))
            self.tformat = config.get('Timeseries', 'strftime')
        except (IOError, ConfigParser.Error):
            self.tformat = def_tformat



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

        Used when the content atom is `TimeAtom`.
        """

        try:
            return time.strftime(self.tformat, time.gmtime(content))
        except ValueError:
            return content


    def formatScikitsTS(self, value):
        """Format a given date in a user friendly way.

        Only Date instances (generated via ``scikits.timeseries`` module) are
        formatted with this method.

        :Parameter value: the content of the table cell being formatted
        """

        date = ts.Date(self.freq, value=int(value))
        try:
            return date.datetime.strftime(self.tformat)
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
            return None
        cell = self.rbuffer.getCell(self.rbuffer.start + index.row(), 
            index.column())
        if role == QtCore.Qt.DisplayRole:
            if index.column() in self.time_cols:
                return self.formatTime(cell)
            return vitables.utils.formatArrayContent(cell)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        else:
            return None


    def rowCount(self, index):
        """The number of rows under the given index.

        When implementing a table based model this method has to be overriden
        -because it is an abstract method- and should return 0 for valid
        indices (because they have no children). If the index is not valid the 
        method  should return the number of rows exposed by the model.

        :Parameter index: the model index being inspected.
        """

        if not index.isValid():
            return self.numrows
        else:
            return 0


    def columnCount(self, index):
        """The number of columns of the given model index.

        When implementing a table based model this method has to be overriden
        -because it is an abstract method- and should return 0 for valid
        indices (because they have no children). If the index is not valid the 
        method  should return the number of columns exposed by the model.

        :Parameter index: the model index being inspected.
        """

        if not index.isValid():
            return self.numcols
        else:
            return 0
