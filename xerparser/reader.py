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


"""
This file starts the process of reading and parsing xer files

"""

import csv
import io
import mmap
import codecs
from xerparser import *
from typing import List
from xerparser.exceptions import XerParseError
from xerparser.model.classes.data import Data
from xerparser.write import writeXER
import sys

csv.field_size_limit(sys.maxsize)


def _decode_xer_bytes(raw: bytes) -> str:
    """Decode raw XER bytes once, preserving every character.

    Ladder: BOM (utf-8/utf-16) -> utf-8 strict -> cp1252 strict ->
    cp1252 with replacement (never-fail floor). utf-8 is tried before cp1252
    because its strict multi-byte structure is a reliable detector, so genuine
    utf-8 files decode correctly; cp1252 is P6's default for Western text.
    Non-Western codecs (CJK/Cyrillic) degrade to mojibake but are never
    deleted — scheduling fields are all ASCII, so only labels garble.
    """
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig")
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return raw.decode("utf-16")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


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

    current_table = ""
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
        print("Number of activities: ", self.tasks.count)
        print("Number of relationships: ", len(TaskPred.obj_list))

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

    def __init__(self, filename):
        self.file = filename
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
        self._data.predecessors = self._predecessors
        with open(filename, "rb") as fh:
            text = _decode_xer_bytes(fh.read())
        # A complete export always ends with an %E marker. Pre-scan for it so a
        # short final row (a mid-row cut) reports as truncation, while a short
        # row inside an otherwise-complete file reports as raggedness.
        has_end_marker = any(line.startswith("%E") for line in text.splitlines())
        current_table = ""
        current_headers = []
        stream = csv.reader(io.StringIO(text), delimiter="\t")
        for row in stream:
            if not row:  # Skip empty rows
                continue
            if row[0] == "%T":
                current_table = row[1]
            elif row[0] == "%F":
                current_headers = [r.strip() for r in row[1:]]
            elif row[0] == "%R":
                if len(row) - 1 != len(current_headers):
                    if has_end_marker:
                        raise XerParseError(
                            "ragged_row",
                            f"{len(row) - 1} fields vs {len(current_headers)} headers",
                            current_table,
                            stream.line_num,
                        )
                    raise XerParseError(
                        "truncated", "file cut off mid-row (no %E end marker)"
                    )
                zipped_record = dict(zip(current_headers, row[1:]))
                try:
                    self.create_object(current_table, zipped_record)
                except XerParseError:
                    raise
                except Exception as e:
                    raise XerParseError(
                        "malformed_row", str(e), current_table, stream.line_num
                    ) from e
        if not has_end_marker:
            raise XerParseError("truncated", "missing %E end marker")

        # for line in content:
        #     line_lst = line.split('\t')
        #     if line_lst[0] == "%T":
        #         current_table = line_lst[1]
        #     elif line_lst[0] == "%R":
        #         self.create_object(current_table, line_lst[1:])

    def get_num_lines(self, file_path):
        fp = open(file_path, "r+")
        buf = mmap.mmap(fp.fileno(), 0)
        lines = 0
        while buf.readline():
            lines += 1
        return lines
