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
Type definitions for PyP6XER.

This module provides type aliases, protocols, and typed dictionaries
for improved type safety throughout the library.
"""

from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    runtime_checkable,
)

# Type aliases for common types
TaskId = int
ProjectId = int
WbsId = int
CalendarId = int
ResourceId = int
RelationshipId = int

# Duration in hours
DurationHours = float

# Percentage (0-100)
Percentage = float

# Generic type for parameter dictionaries
ParamDict = Dict[str, Optional[str]]


# =============================================================================
# Status and Type Literals
# =============================================================================

# Activity status codes
ActivityStatus = Literal['TK_NotStart', 'TK_Active', 'TK_Complete']

# Task types
TaskType = Literal['TT_Task', 'TT_Rsrc', 'TT_LOE', 'TT_Mile', 'TT_FinMile', 'TT_WBS']

# Duration types
DurationType = Literal['DT_FixedDrtn', 'DT_FixedUnits', 'DT_FixedDUR2', 'DT_FixedRate']

# Percent complete types
PercentCompleteType = Literal['CP_Phys', 'CP_Drtn', 'CP_Units']

# Constraint types
ConstraintType = Literal[
    'CS_MEO', 'CS_MEOA', 'CS_MSO', 'CS_MSOA', 'CS_MSOB',
    'CS_ALAP', 'CS_MANDSTART', 'CS_MANDFIN', None
]

# Relationship types
RelationshipType = Literal['PR_FS', 'PR_FF', 'PR_SS', 'PR_SF']

# Resource types
ResourceType = Literal['RT_Labor', 'RT_Equip', 'RT_Mat']


# =============================================================================
# TypedDicts for Parameter Dictionaries
# =============================================================================

class TaskParams(TypedDict, total=False):
    """Type definition for task parameter dictionary."""
    task_id: str
    proj_id: str
    wbs_id: str
    clndr_id: str
    phys_complete_pct: str
    rev_fdbk_flag: str
    est_wt: str
    lock_plan_flag: str
    auto_compute_act_flag: str
    complete_pct_type: str
    task_type: str
    duration_type: str
    status_code: str
    task_code: str
    task_name: str
    rsrc_id: str
    total_float_hr_cnt: str
    free_float_hr_cnt: str
    remain_drtn_hr_cnt: str
    act_work_qty: str
    remain_work_qty: str
    target_work_qty: str
    target_drtn_hr_cnt: str
    target_equip_qty: str
    act_equip_qty: str
    remain_equip_qty: str
    cstr_date: str
    act_start_date: str
    act_end_date: str
    late_start_date: str
    late_end_date: str
    expect_end_date: str
    early_start_date: str
    early_end_date: str
    restart_date: str
    reend_date: str
    target_start_date: str
    target_end_date: str
    rem_late_start_date: str
    rem_late_end_date: str
    cstr_type: str
    priority_type: str
    suspend_date: str
    resume_date: str
    int_path: str
    int_path_order: str
    guid: str
    tmpl_guid: str
    cstr_date2: str
    cstr_type2: str
    driving_path_flag: str
    act_this_per_work_qty: str
    act_this_per_equip_qty: str
    external_early_start_date: str
    external_late_end_date: str
    create_date: str
    update_date: str
    create_user: str
    update_user: str
    location_id: str


class ProjectParams(TypedDict, total=False):
    """Type definition for project parameter dictionary."""
    proj_id: str
    fy_start_month_num: str
    rsrc_self_add_flag: str
    allow_complete_flag: str
    rsrc_multi_assign_flag: str
    checkout_flag: str
    project_flag: str
    step_complete_flag: str
    cost_qty_recalc_flag: str
    batch_sum_flag: str
    name_sep_char: str
    def_complete_pct_type: str
    proj_short_name: str
    acct_id: str
    orig_proj_id: str
    source_proj_id: str
    base_type_id: str
    clndr_id: str
    sum_base_proj_id: str
    task_code_base: str
    task_code_step: str
    priority_num: str
    wbs_max_sum_level: str
    strgy_priority_num: str
    last_recalc_date: str
    plan_start_date: str
    plan_end_date: str
    scd_end_date: str
    add_date: str
    last_tasksum_date: str
    fcst_start_date: str
    def_duration_type: str
    task_code_prefix: str
    guid: str
    def_qty_type: str
    add_by_name: str
    web_local_root_path: str
    proj_url: str
    def_rate_type: str
    add_act_remain_flag: str
    act_this_per_link_flag: str
    def_task_type: str
    act_pct_link_flag: str
    critical_path_type: str
    task_code_prefix_flag: str
    def_rollup_dates_flag: str
    use_project_baseline_flag: str
    rem_target_link_flag: str
    reset_planned_flag: str
    allow_neg_act_flag: str
    sum_assign_level: str
    last_fin_dates_id: str
    last_baseline_update_date: str
    cr_external_key: str
    apply_actuals_date: str
    location_id: str
    loaded_scope_level: str
    export_flag: str
    new_fin_dates_id: str
    baselines_to_export: str
    baseline_names_to_export: str
    next_data_date: str
    close_period_flag: str
    sum_refresh_date: str
    trsrcsum_loaded: str
    sumtask_loaded: str
    fintmpl_id: str


class RelationshipParams(TypedDict, total=False):
    """Type definition for relationship parameter dictionary."""
    task_pred_id: str
    task_id: str
    pred_task_id: str
    proj_id: str
    pred_proj_id: str
    pred_type: str
    lag_hr_cnt: str
    float_path: str
    aref: str
    arls: str
    comments: str


class CalendarParams(TypedDict, total=False):
    """Type definition for calendar parameter dictionary."""
    clndr_id: str
    default_flag: str
    clndr_name: str
    proj_id: str
    base_clndr_id: str
    last_chng_date: str
    clndr_type: str
    day_hr_cnt: str
    week_hr_cnt: str
    month_hr_cnt: str
    year_hr_cnt: str
    rsrc_private: str
    clndr_data: str


class ResourceParams(TypedDict, total=False):
    """Type definition for resource parameter dictionary."""
    rsrc_id: str
    parent_rsrc_id: str
    clndr_id: str
    role_id: str
    shift_id: str
    user_id: str
    pobs_id: str
    rsrc_seq_num: str
    email_addr: str
    employee_code: str
    office_phone: str
    other_phone: str
    rsrc_name: str
    rsrc_short_name: str
    rsrc_title_name: str
    def_qty_per_hr: str
    cost_qty_type: str
    ot_factor: str
    active_flag: str
    auto_compute_act_flag: str
    def_cost_qty_link_flag: str
    ot_flag: str
    rsrc_type: str
    location_id: str
    rsrc_notes: str
    load_tasks_flag: str
    level_flag: str
    last_checksum: str


# =============================================================================
# Protocols for Duck Typing
# =============================================================================

@runtime_checkable
class HasId(Protocol):
    """Protocol for objects with an id property."""
    @property
    def id(self) -> int: ...


@runtime_checkable
class HasTaskId(Protocol):
    """Protocol for objects with a task_id attribute."""
    task_id: int


@runtime_checkable
class HasProjectId(Protocol):
    """Protocol for objects with a proj_id attribute."""
    proj_id: int


@runtime_checkable
class Exportable(Protocol):
    """Protocol for objects that can be exported to TSV format."""
    def get_tsv(self) -> List[Any]: ...


@runtime_checkable
class Collection(Protocol[TypeVar('T')]):
    """Protocol for collection classes."""
    def add(self, params: ParamDict, data: Any = None) -> None: ...
    def get_tsv(self) -> List[List[Any]]: ...
    def __len__(self) -> int: ...
    def __iter__(self): ...


# =============================================================================
# Result Types
# =============================================================================

class ConstraintInfo(TypedDict):
    """Type definition for constraint information dictionary."""
    ConstraintType: str
    ConstraintDate: datetime


class ActivityInfo(TypedDict):
    """Type definition for activity information dictionary."""
    id: str
    name: str
    duration: Optional[float]
    tf: float


class RelationshipInfo(TypedDict):
    """Type definition for relationship information dictionary."""
    successor: Optional[ActivityInfo]
    predecessor: Optional[ActivityInfo]
    type: str
    lag: int


# =============================================================================
# Analysis Result Types
# =============================================================================

class AnalysisSummary(TypedDict):
    """Type definition for analysis summary."""
    activity_cnt: int
    relationship_cnt: int


class AnalysisMetric(TypedDict):
    """Type definition for analysis metric with count and percentage."""
    cnt: int
    activities: List[Optional[ActivityInfo]]
    pct: float


class RelationshipMetric(TypedDict):
    """Type definition for relationship analysis metric."""
    cnt: int
    relations: List[RelationshipInfo]
    pct: float


class DCMA14Results(TypedDict):
    """Type definition for DCMA 14-point analysis results."""
    analysis: Dict[str, Any]
