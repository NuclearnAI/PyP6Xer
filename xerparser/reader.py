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
from typing import List
import sys

from xerparser.exceptions import XerParseError
from xerparser.model.classes.data import Data
from xerparser.model.classes.taskpred import TaskPred  # re-exported; used by summary()
from xerparser.model.classes.projcat import ProjCat
from xerparser.model.classes.taskproc import TaskProc
from xerparser.model.classes.fintmpl import FinTmpl
from xerparser.model.classes.nonwork import NonWork
from xerparser.model.classes.task import Task
from xerparser.write import writeXER
from xerparser.model.tasks import Tasks
from xerparser.model.predecessors import Predecessors
from xerparser.model.projects import Projects
from xerparser.model.wbss import WBSs
from xerparser.model.resources import Resources
from xerparser.model.accounts import Accounts
from xerparser.model.activitycodes import ActivityCodes
from xerparser.model.acttypes import ActTypes
from xerparser.model.calendars import Calendars
from xerparser.model.currencies import Currencies
from xerparser.model.obss import OBSs
from xerparser.model.rcattypes import RCatTypes
from xerparser.model.rcatvals import RCatVals
from xerparser.model.rolerates import RoleRates
from xerparser.model.roles import Roles
from xerparser.model.rsrccurves import ResourceCurves
from xerparser.model.rsrcrates import ResourceRates
from xerparser.model.rsrccats import ResourceCategories
from xerparser.model.schedoptions import SchedOptions
from xerparser.model.activitiyresources import ActivityResources
from xerparser.model.udfvalues import UDFValues
from xerparser.model.udftypes import UDFTypes
from xerparser.model.taskactvs import TaskActvs
from xerparser.model.pacttypes import PCatTypes
from xerparser.model.pcatvals import PCatVals
from xerparser.model.projcats import ProjCats
from xerparser.model.taskprocs import TaskProcs
from xerparser.model.fintmpls import FinTmpls
from xerparser.model.nonworks import NonWorks

csv.field_size_limit(sys.maxsize)


def _decode_xer_bytes(raw: bytes) -> str:
    """Decode raw XER bytes once, preserving every character.

    Ladder: BOM (utf-8/utf-32/utf-16) -> utf-8 strict -> cp1252 strict ->
    cp1252 with replacement (never-fail floor). utf-8 is tried before cp1252
    because its strict multi-byte structure is a reliable detector, so genuine
    utf-8 files decode correctly; cp1252 is P6's default for Western text.
    Non-Western codecs (CJK/Cyrillic) degrade to mojibake but are never
    deleted — scheduling fields are all ASCII, so only labels garble.
    """
    # BOM branches fall through to the ladder (not return) so a BOM-tagged file
    # with a stray bad byte still reaches the never-fail cp1252 floor.
    # UTF-32-LE (\xff\xfe\x00\x00) is checked before UTF-16-LE (\xff\xfe) — the
    # latter is a prefix of the former, so order matters.
    if raw.startswith(codecs.BOM_UTF8):
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass
    elif raw.startswith(codecs.BOM_UTF32_LE) or raw.startswith(codecs.BOM_UTF32_BE):
        try:
            return raw.decode("utf-32")
        except UnicodeDecodeError:
            pass
    elif raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        try:
            return raw.decode("utf-16")
        except UnicodeDecodeError:
            pass
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
        Create and add an object to the appropriate collection based on object type.

        Args:
            object_type: The XER record type (e.g., 'PROJECT', 'TASK', etc.)
            params: Dictionary of field values for the record

        Returns:
            None
        """
        object_type = object_type.strip()

        if object_type in self._simple_handlers:
            self._simple_handlers[object_type].add(params)
        elif object_type in self._data_handlers:
            self._data_handlers[object_type].add(params, self._data)

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
        # Truncation is a soft signal: consumers that build one precedence
        # network (sim) reject it; aggregating consumers (training) proceed.
        self.truncated = False
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
        # Built once (not per record): create_object dispatch by object_type.
        self._simple_handlers = {
            "CURRTYPE": self._currencies,
            "ROLES": self._roles,
            "ACCOUNT": self._accounts,
            "ROLERATE": self._rolerates,
            "OBS": self._obss,
            "RCATTYPE": self._rcattypes,
            "UDFTYPE": self._udftypes,
            "RCATVAL": self._rcatvals,
            "CALENDAR": self._calendars,
            "SCHEDOPTIONS": self._schedoptions,
            "RSRC": self._resources,
            "RSRCCURVDATA": self._rsrcurves,
            "ACTVTYPE": self._acttypes,
            "PCATTYPE": self._pcattypes,
            "PROJPCAT": self._projpcats,
            "PCATVAL": self._pcatvals,
            "RSRCRATE": self._rsrcrates,
            "RSRCRCAT": self._rsrccats,
            "ACTVCODE": self._actvcodes,
            "TASKPRED": self._predecessors,
            "TASKPROC": self._taskprocs,
            "UDFVALUE": self._udfvalues,
            "FINTMPL": self._fintmpls,
            "NONWORK": self._nonworks,
        }
        self._data_handlers = {
            "PROJECT": self._projects,
            "PROJWBS": self._wbss,
            "TASK": self._tasks,
            "TASKRSRC": self._activityresources,
            "TASKACTV": self._activitycodes,
        }
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
        # Structural policy: field-count variance in data rows is tolerated (zip,
        # like the original parser) -- a short row leaves trailing columns unset,
        # a long row drops the surplus. We fail loud only on a genuinely malformed
        # value (create_object) or an unroutable %T; a missing %E end marker sets
        # the soft truncated flag.
        saw_end_marker = False
        current_table = ""
        current_headers = []
        # XER is plain TSV with no quoting convention; QUOTE_NONE stops a value
        # that contains a `"` from being read as a quoted field and silently
        # swallowing following rows. newline="" lets csv handle line endings.
        stream = csv.reader(
            io.StringIO(text, newline=""), delimiter="\t", quoting=csv.QUOTE_NONE
        )
        for row in stream:
            if not row:  # Skip empty rows
                continue
            tag = row[0]
            if tag == "%T":
                if len(row) < 2:
                    # A %T with no table name is unroutable structure; fail loud
                    # instead of an uncaught IndexError escaping the error contract.
                    raise XerParseError(
                        "ragged_row", "table row missing name", current_table, stream.line_num
                    )
                current_table = row[1]
                current_headers = []
            elif tag == "%F":
                current_headers = [r.strip() for r in row[1:]]
            elif tag == "%E":
                saw_end_marker = True
            elif tag == "%R":
                if not current_headers:
                    # A data row with no %F header for its table is unroutable
                    # (values can't be mapped to fields); fail loud rather than
                    # silently zipping against an empty header list.
                    raise XerParseError(
                        "ragged_row", "data row before %F header", current_table, stream.line_num
                    )
                zipped_record = dict(zip(current_headers, row[1:]))
                try:
                    self.create_object(current_table, zipped_record)
                except Exception as e:
                    raise XerParseError(
                        "malformed_row", str(e), current_table, stream.line_num
                    ) from e
        if not saw_end_marker:
            # No end marker => the file was cut before %E (truncation).
            self.truncated = True

        # for line in content:
        #     line_lst = line.split('\t')
        #     if line_lst[0] == "%T":
        #         current_table = line_lst[1]
        #     elif line_lst[0] == "%R":
        #         self.create_object(current_table, line_lst[1:])

    def get_num_lines(self, file_path):
        # Read-only open + ACCESS_READ so counting lines never requires write
        # permission on the file.
        with open(file_path, "rb") as fp:
            buf = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)
            lines = 0
            while buf.readline():
                lines += 1
            buf.close()
        return lines
