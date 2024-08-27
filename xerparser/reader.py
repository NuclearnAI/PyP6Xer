# PyP6XER
# Copyright (C) 2020, 2021 Hassan Emam <hassan@constology.com>
#
# This file is part of PyP6XER.
#
# PyP6XER library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License v2.1 as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyP6XER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyP6XER.  If not, see <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html>.


'''
This file starts the process of reading and parsing xer files

'''
import csv
import mmap
import codecs
from xerparser import *
from typing import List
from xerparser.model.classes.data import Data
from xerparser.write import writeXER
import sys
from typing import Union
import io
import re

csv.field_size_limit(sys.maxsize)


class Reader:

    """
    Reader class is the main parser for xer files. It takes a file path as a parameter.
    The read records are parsed into classes depending on their types like activities, wbs,etc.

    :param <file>: is an xer file that need to be parsed
    :return: Reader object that contains collection of parsed records
    :Example:

    from xerparser.reader import Reader
    file = Reader('file.xer')

    """

    current_table = ''
    current_headers = []

    def write(self, filename=None):
        if filename is None:
            raise Exception("You have to provide the filename")
        writeXER(self, filename)

    def create_object(self, object_type, params):
        """

        Args:
            object_type:
            params:

        Returns:

        """
        if object_type.strip() == "CURRTYPE":
            self._currencies.add(params)
        elif object_type.strip() == "ROLES":
            self._roles.add(params)
        elif object_type.strip() == "ACCOUNT":
            self._accounts.add(params)
        elif object_type.strip() == "ROLERATE":
            self._rolerates.add(params)
        elif object_type.strip() == "OBS":
            self._obss.add(params)
        elif object_type.strip() == "RCATTYPE":
            self._rcattypes.add(params)
        elif object_type.strip() == "UDFTYPE":
            self._udftypes.add(params)
        elif object_type.strip() == "RCATVAL":
            self._rcatvals.add(params)
        elif object_type.strip() == "PROJECT":
            self._projects.add(params, self._data)
        elif object_type.strip() == "CALENDAR":
            self._calendars.add(params)
        elif object_type.strip() == "SCHEDOPTIONS":
            self._schedoptions.add(params)
        elif object_type.strip() == "PROJWBS":
            self._wbss.add(params, self._data)
        elif object_type.strip() == "RSRC":
            self._resources.add(params)
        elif object_type.strip() == "RSRCCURVDATA":
            self._rsrcurves.add(params)
        elif object_type.strip() == "ACTVTYPE":
            self._acttypes.add(params)
        elif object_type.strip() == "PCATTYPE":
            self._pcattypes.add(params)
        elif object_type.strip() == "PROJPCAT":
            self._projpcats.add(params)
        elif object_type.strip() == "PCATVAL":
            self._pcatvals.add(params)
        elif object_type.strip() == "RSRCRATE":
            self._rsrcrates.add(params)
        elif object_type.strip() == "RSRCRCAT":
            self._rsrccats.add(params)
        elif object_type.strip() == "TASK":
            self._tasks.add(params, self._data)
        elif object_type.strip() == "ACTVCODE":
            self._actvcodes.add(params)
        elif object_type.strip() == "TASKPRED":
            self._predecessors.add(params)
        elif object_type.strip() == "TASKRSRC":
            self._activityresources.add(params, self._data)
        elif object_type.strip() == "TASKPROC":
            self._taskprocs.add(params)
        elif object_type.strip() == "TASKACTV":
            self._activitycodes.add(params, self._data)
        elif object_type.strip() == "UDFVALUE":
            self._udfvalues.add(params)
        elif object_type.strip() == "FINTMPL":
            self._fintmpls.add(params)
        elif object_type.strip() == "NONWORK":
            self._nonworks.add(params)

    def summary(self):
        print('Number of activities: ', self.tasks.count)
        print('Number of relationships: ', len(TaskPred.obj_list))

    @property
    def projects(self) -> Projects:
        """
        Projects

        :return: list of all projects contained in the xer file

        todo:: text

        """
        return self._projects

    @property
    def activities(self) -> Tasks:
        """
        Property to retrieve list of tasks
        Returns: list of tasks
        """
        return self._tasks

    @property
    def wbss(self) -> WBSs:
        """
        Property to return all wbs elements in the parsed file
        Returns:
            list of wbs elements
        """
        return self._wbss

    @property
    def relations(self) -> Predecessors:
        """
        Property to retrieve relationships from parsed file
        Returns:
            list of relations
        """
        return self._predecessors

    @property
    def resources(self) -> Resources:
        """
        Property to return a list of resources from parsed file
        Returns:
            list of resources of type Resources
        """
        return self._resources

    @property
    def accounts(self) -> Accounts:
        """
        Property to return a list of accounts from parsed files
        Returns:
            list of accounts of type Accounts
        """
        return self._accounts

    @property
    def activitycodes(self) -> ActivityCodes:
        """
        Property to return a list of activity codes from parsed files
        Returns:
            list of accounts of type ActivityCode

        """
        return self._activitycodes
    @property
    def actvcodes(self) -> TaskActvs:
        return self._actvcodes

    @property
    def acttypes(self) -> ActTypes:
        return self._acttypes

    @property
    def calendars(self) -> Calendars:
        return self._calendars

    @property
    def currencies(self) -> Currencies:
        return self._currencies

    @property
    def obss(self) -> OBSs:
        return self._obss

    @property
    def rcattypes(self) -> RCatTypes:
        return self._rcattypes

    @property
    def rcatvals(self) -> RCatVals:
        return self._rcatvals

    @property
    def rolerates(self) -> RoleRates:
        return self._rolerates

    @property
    def roles(self) -> Roles:
        return self._roles

    @property
    def resourcecurves(self) -> ResourceCurves:
        return self._rsrcurves

    @property
    def resourcerates(self) -> ResourceRates:
        return self._rsrcrates

    @property
    def resourcecategories(self) -> ResourceCategories:
        return self._rsrccats

    @property
    def scheduleoptions(self) -> SchedOptions:
        return self._schedoptions

    @property
    def activityresources(self) -> ActivityResources:
        return self._activityresources

    @property
    def udfvalues(self) -> UDFValues:
        return self._udfvalues

    @property
    def udftypes(self) -> UDFTypes:
        return self._udftypes

    @property
    def pcattypes(self) -> List[PCatTypes]:
        return self._pcattypes

    @property
    def pcatvals(self) -> List[PCatVals]:
        return self._pcatvals

    @property
    def projpcats(self) -> List[ProjCat]:
        return self._projpcats

    @property
    def taskprocs(self) -> List[TaskProc]:
        return self._taskprocs

    @property
    def fintmpls(self) -> List[FinTmpl]:
        return self._fintmpls

    @property
    def nonworks(self) -> List[NonWork]:
        return self._nonworks

    def __init__(self, file_or_stream: Union[str, bytes]):
        self._tasks = Tasks()
        self._predecessors = Predecessors()
        self._projects = Projects()
        self._wbss = WBSs()
        self._resources = Resources()
        self._accounts = Accounts()
        self._actvcodes = ActivityCodes()
        self._activitycodes = TaskActvs()
        self._acttypes = ActTypes()
        self._calendars = Calendars()
        self._currencies = Currencies()
        self._obss = OBSs()
        self._rcatvals = RCatVals()
        self._rcattypes = RCatTypes()
        self._rolerates = RoleRates()
        self._roles = Roles()
        self._rsrcurves = ResourceCurves()
        self._rsrcrates = ResourceRates()
        self._rsrccats = ResourceCategories()
        self._schedoptions = SchedOptions()
        self._activityresources = ActivityResources()
        self._udftypes = UDFTypes()
        self._udfvalues = UDFValues()
        self._pcattypes = PCatTypes()
        self._pcatvals = PCatVals()
        self._projpcats = ProjCats()
        self._taskprocs = TaskProcs()
        self._fintmpls = FinTmpls()
        self._nonworks = NonWorks()
        self._data = Data()
        self._data.projects = self._projects
        self._data.wbss = self._wbss
        self._data.tasks = self._tasks
        self._data.resources = self._resources
        self._data.taskresource = self._activityresources
        self._data.taskactvcodes = self._activitycodes

        # Determine if input is a file path (str) or a byte stream (bytes)
        if isinstance(file_or_stream, str):
            # Treat as a file path, open with universal-newline mode
            with codecs.open(file_or_stream, encoding='utf-8', errors='ignore') as tsvfile:
                self._parse_stream(tsvfile)
        elif isinstance(file_or_stream, bytes):
            # Attempt to decode with UTF-8 first
            try:
                decoded_stream = file_or_stream.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                # If UTF-8 fails, try a different encoding like ISO-8859-1 or fallback to ASCII
                raise ValueError("Invalid input: could not decode byte stream")
            # use newline=None to handle new-line characters within fields and ensure files from linux and windows are parsed correctly
            text_stream = io.StringIO(decoded_stream, newline=None)
            self._parse_stream(text_stream)
        else:
            raise ValueError("Invalid input: must be a file path or a byte stream")
        
    def _parse_stream(self, text_stream):
        # Use a custom quote handling method and handle new-line characters manually
        reader = csv.reader(text_stream, delimiter='\t')
        for row in reader:
            try:
                if not row:  # Skip empty rows
                    print("Warning: Empty row detected on row %s" % reader.line_num)
                    continue
                if row[0] == "%T":
                    self.current_table = row[1]
                elif row[0] == "%F":
                    self.current_headers = [r.strip() for r in row[1:]]
                elif row[0] == "%R":
                    zipped_record = dict(zip(self.current_headers, row[1:]))
                    self.create_object(self.current_table, zipped_record)
            except Exception as e:
                print("Error reading line %s: %s" % (reader.line_num, e))
                raise e

    def _preprocess_stream(self, stream_content):
        """
        Preprocess the stream content to handle new-line characters within fields.
        Replace new-lines within fields with a space or another character.
        """
        # Replace new-line characters within fields with a space
        # This regex looks for new-lines that are not preceded or followed by another new-line (which would indicate a legitimate new line)
        return re.sub(r'(?<!\r)\n(?!\r)', ' ', stream_content)

    def get_num_lines(self, file_path):
        fp = open(file_path, "r+")
        buf = mmap.mmap(fp.fileno(), 0)
        lines = 0
        while buf.readline():
            lines += 1
        return lines
