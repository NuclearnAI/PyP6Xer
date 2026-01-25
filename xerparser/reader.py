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
import mmap
import codecs
import warnings
from typing import List
import sys

from xerparser.model.classes.data import Data
from xerparser.model.classes.taskpred import TaskPred
from xerparser.model.classes.projcat import ProjCat
from xerparser.model.classes.taskproc import TaskProc
from xerparser.model.classes.fintmpl import FinTmpl
from xerparser.model.classes.nonwork import NonWork
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

        # Dispatch table for handlers that don't need data parameter
        simple_handlers = {
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

        # Dispatch table for handlers that need data parameter
        data_handlers = {
            "PROJECT": self._projects,
            "PROJWBS": self._wbss,
            "TASK": self._tasks,
            "TASKRSRC": self._activityresources,
            "TASKACTV": self._activitycodes,
        }

        if object_type in simple_handlers:
            simple_handlers[object_type].add(params)
        elif object_type in data_handlers:
            data_handlers[object_type].add(params, self._data)

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
        with codecs.open(filename, encoding="utf-8", errors="ignore") as tsvfile:
            stream = csv.reader(tsvfile, delimiter="\t")
            for row in stream:
                try:
                    if not row:  # Skip empty rows
                        warnings.warn(f"Empty row detected on row {stream.line_num}")
                        continue
                    if row[0] == "%T":
                        current_table = row[1]
                    elif row[0] == "%F":
                        current_headers = [r.strip() for r in row[1:]]
                    elif row[0] == "%R":
                        zipped_record = dict(zip(current_headers, row[1:]))
                        self.create_object(current_table, zipped_record)
                except Exception as e:
                    print("Error reading line %s: %s", stream.line_num, e)
                    raise e

        # for line in content:
        #     line_lst = line.split('\t')
        #     if line_lst[0] == "%T":
        #         current_table = line_lst[1]
        #     elif line_lst[0] == "%R":
        #         self.create_object(current_table, line_lst[1:])

    def get_num_lines(self, file_path):
        with open(file_path, "r+") as fp:
            buf = mmap.mmap(fp.fileno(), 0)
            lines = 0
            while buf.readline():
                lines += 1
            buf.close()
        return lines
