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
Validation utilities for XER data parsing and integrity checking.

This module provides:
- Type conversion helpers with validation
- Data validation functions
- XER file structure validation
- Schedule integrity checks
"""

from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)
from dataclasses import dataclass, field
from enum import Enum
import re


T = TypeVar('T')


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue found in XER data."""
    severity: ValidationSeverity
    code: str
    message: str
    location: Optional[str] = None
    field: Optional[str] = None
    value: Optional[Any] = None

    def __str__(self) -> str:
        parts = [f"[{self.severity.value.upper()}] {self.code}: {self.message}"]
        if self.location:
            parts.append(f" at {self.location}")
        if self.field:
            parts.append(f" (field: {self.field})")
        return "".join(parts)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Return only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Return only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add an issue to the result."""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.is_valid = False

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        self.issues.extend(other.issues)
        if not other.is_valid:
            self.is_valid = False


# =============================================================================
# Type Conversion Helpers with Validation
# =============================================================================

def parse_int(
    value: Optional[str],
    field_name: str = "value",
    default: Optional[int] = None,
    allow_empty: bool = True
) -> Optional[int]:
    """
    Safely parse a string to an integer with validation.

    Args:
        value: The string value to parse
        field_name: Name of the field for error messages
        default: Default value if parsing fails
        allow_empty: Whether to allow empty/None values

    Returns:
        Parsed integer or default value

    Raises:
        ValueError: If value is invalid and no default provided
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_empty:
            return default
        raise ValueError(f"{field_name} cannot be empty")

    try:
        return int(str(value).strip())
    except (ValueError, TypeError) as e:
        if default is not None:
            return default
        raise ValueError(f"Invalid integer value for {field_name}: '{value}'") from e


def parse_float(
    value: Optional[str],
    field_name: str = "value",
    default: Optional[float] = None,
    allow_empty: bool = True,
    use_locale: bool = False
) -> Optional[float]:
    """
    Safely parse a string to a float with validation.

    Args:
        value: The string value to parse
        field_name: Name of the field for error messages
        default: Default value if parsing fails
        allow_empty: Whether to allow empty/None values
        use_locale: Whether to use locale-aware parsing

    Returns:
        Parsed float or default value
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_empty:
            return default
        raise ValueError(f"{field_name} cannot be empty")

    try:
        if use_locale:
            import locale
            return locale.atof(str(value).strip())
        return float(str(value).strip())
    except (ValueError, TypeError) as e:
        if default is not None:
            return default
        raise ValueError(f"Invalid float value for {field_name}: '{value}'") from e


def parse_datetime(
    value: Optional[str],
    field_name: str = "value",
    format: str = '%Y-%m-%d %H:%M',
    default: Optional[datetime] = None,
    allow_empty: bool = True
) -> Optional[datetime]:
    """
    Safely parse a string to a datetime with validation.

    Args:
        value: The string value to parse
        field_name: Name of the field for error messages
        format: Expected datetime format
        default: Default value if parsing fails
        allow_empty: Whether to allow empty/None values

    Returns:
        Parsed datetime or default value
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_empty:
            return default
        raise ValueError(f"{field_name} cannot be empty")

    try:
        return datetime.strptime(str(value).strip(), format)
    except (ValueError, TypeError) as e:
        if allow_empty or default is not None:
            return default
        raise ValueError(f"Invalid datetime value for {field_name}: '{value}' (expected format: {format})") from e


def parse_string(
    value: Optional[str],
    field_name: str = "value",
    default: Optional[str] = None,
    strip: bool = True,
    allow_empty: bool = True,
    max_length: Optional[int] = None
) -> Optional[str]:
    """
    Safely parse and validate a string value.

    Args:
        value: The string value to process
        field_name: Name of the field for error messages
        default: Default value if empty
        strip: Whether to strip whitespace
        allow_empty: Whether to allow empty values
        max_length: Maximum allowed length

    Returns:
        Processed string or default value
    """
    if value is None:
        if allow_empty:
            return default
        raise ValueError(f"{field_name} cannot be None")

    result = str(value)
    if strip:
        result = result.strip()

    if not result:
        if allow_empty:
            return default
        raise ValueError(f"{field_name} cannot be empty")

    if max_length and len(result) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")

    return result


def parse_bool(
    value: Optional[str],
    field_name: str = "value",
    default: Optional[bool] = None,
    true_values: Set[str] = None,
    false_values: Set[str] = None
) -> Optional[bool]:
    """
    Safely parse a string to a boolean with validation.

    Args:
        value: The string value to parse
        field_name: Name of the field for error messages
        default: Default value if parsing fails
        true_values: Set of values considered True
        false_values: Set of values considered False

    Returns:
        Parsed boolean or default value
    """
    if true_values is None:
        true_values = {'Y', 'y', 'yes', 'Yes', 'YES', 'true', 'True', 'TRUE', '1'}
    if false_values is None:
        false_values = {'N', 'n', 'no', 'No', 'NO', 'false', 'False', 'FALSE', '0'}

    if value is None or (isinstance(value, str) and not value.strip()):
        return default

    str_value = str(value).strip()
    if str_value in true_values:
        return True
    if str_value in false_values:
        return False

    if default is not None:
        return default
    raise ValueError(f"Invalid boolean value for {field_name}: '{value}'")


# =============================================================================
# XER Data Validators
# =============================================================================

class XERValidator:
    """Validator for XER file data and structure."""

    # Valid XER record types
    VALID_RECORD_TYPES: Set[str] = {
        'CURRTYPE', 'ROLES', 'ACCOUNT', 'ROLERATE', 'OBS', 'RCATTYPE',
        'UDFTYPE', 'RCATVAL', 'PROJECT', 'CALENDAR', 'SCHEDOPTIONS',
        'PROJWBS', 'RSRC', 'RSRCCURVDATA', 'ACTVTYPE', 'PCATTYPE',
        'PROJPCAT', 'PCATVAL', 'RSRCRATE', 'RSRCRCAT', 'TASK',
        'ACTVCODE', 'TASKPRED', 'TASKRSRC', 'TASKPROC', 'TASKACTV',
        'UDFVALUE', 'FINTMPL', 'NONWORK'
    }

    # Valid activity status codes
    VALID_STATUS_CODES: Set[str] = {'TK_NotStart', 'TK_Active', 'TK_Complete'}

    # Valid task types
    VALID_TASK_TYPES: Set[str] = {
        'TT_Task', 'TT_Rsrc', 'TT_LOE', 'TT_Mile', 'TT_FinMile', 'TT_WBS'
    }

    # Valid duration types
    VALID_DURATION_TYPES: Set[str] = {
        'DT_FixedDrtn', 'DT_FixedUnits', 'DT_FixedDUR2', 'DT_FixedRate'
    }

    # Valid constraint types
    VALID_CONSTRAINT_TYPES: Set[str] = {
        'CS_MEO', 'CS_MEOA', 'CS_MSO', 'CS_MSOA', 'CS_MSOB',
        'CS_ALAP', 'CS_MANDSTART', 'CS_MANDFIN', None, ''
    }

    # Valid relationship types
    VALID_RELATIONSHIP_TYPES: Set[str] = {'PR_FS', 'PR_FF', 'PR_SS', 'PR_SF'}

    def __init__(self):
        self.result = ValidationResult(is_valid=True)

    def validate_task(self, task_params: Dict[str, Any], task_code: str = "unknown") -> ValidationResult:
        """
        Validate task/activity data.

        Args:
            task_params: Dictionary of task parameters
            task_code: Task code for error messages

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)
        location = f"Task {task_code}"

        # Required fields
        if not task_params.get('task_id'):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="TASK_001",
                message="Task ID is required",
                location=location,
                field="task_id"
            ))

        if not task_params.get('proj_id'):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="TASK_002",
                message="Project ID is required",
                location=location,
                field="proj_id"
            ))

        # Status code validation
        status = task_params.get('status_code', '').strip() if task_params.get('status_code') else None
        if status and status not in self.VALID_STATUS_CODES:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="TASK_003",
                message=f"Unknown status code: {status}",
                location=location,
                field="status_code",
                value=status
            ))

        # Task type validation
        task_type = task_params.get('task_type', '').strip() if task_params.get('task_type') else None
        if task_type and task_type not in self.VALID_TASK_TYPES:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="TASK_004",
                message=f"Unknown task type: {task_type}",
                location=location,
                field="task_type",
                value=task_type
            ))

        # Duration type validation
        dur_type = task_params.get('duration_type', '').strip() if task_params.get('duration_type') else None
        if dur_type and dur_type not in self.VALID_DURATION_TYPES:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="TASK_005",
                message=f"Unknown duration type: {dur_type}",
                location=location,
                field="duration_type",
                value=dur_type
            ))

        # Constraint type validation
        cstr_type = task_params.get('cstr_type', '').strip() if task_params.get('cstr_type') else None
        if cstr_type and cstr_type not in self.VALID_CONSTRAINT_TYPES:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="TASK_006",
                message=f"Unknown constraint type: {cstr_type}",
                location=location,
                field="cstr_type",
                value=cstr_type
            ))

        # Date logic validation
        self._validate_task_dates(task_params, result, location)

        # Duration validation
        self._validate_task_duration(task_params, result, location)

        return result

    def _validate_task_dates(
        self,
        task_params: Dict[str, Any],
        result: ValidationResult,
        location: str
    ) -> None:
        """Validate task date logic."""
        # Parse dates for comparison
        try:
            start = parse_datetime(task_params.get('target_start_date'))
            end = parse_datetime(task_params.get('target_end_date'))

            if start and end and start > end:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="TASK_010",
                    message="Target start date is after target end date",
                    location=location,
                    field="target_start_date"
                ))
        except ValueError:
            pass  # Date parsing handled elsewhere

        # Check actual dates for completed activities
        status = task_params.get('status_code', '').strip() if task_params.get('status_code') else None
        if status == 'TK_Complete':
            if not task_params.get('act_end_date'):
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="TASK_011",
                    message="Completed activity missing actual end date",
                    location=location,
                    field="act_end_date"
                ))

    def _validate_task_duration(
        self,
        task_params: Dict[str, Any],
        result: ValidationResult,
        location: str
    ) -> None:
        """Validate task duration values."""
        try:
            remain_dur = parse_float(task_params.get('remain_drtn_hr_cnt'))
            if remain_dur is not None and remain_dur < 0:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="TASK_020",
                    message="Remaining duration cannot be negative",
                    location=location,
                    field="remain_drtn_hr_cnt",
                    value=remain_dur
                ))
        except ValueError:
            pass

        try:
            target_dur = parse_float(task_params.get('target_drtn_hr_cnt'))
            if target_dur is not None and target_dur < 0:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="TASK_021",
                    message="Target duration cannot be negative",
                    location=location,
                    field="target_drtn_hr_cnt",
                    value=target_dur
                ))
        except ValueError:
            pass

    def validate_relationship(
        self,
        rel_params: Dict[str, Any],
        rel_id: str = "unknown"
    ) -> ValidationResult:
        """
        Validate relationship/predecessor data.

        Args:
            rel_params: Dictionary of relationship parameters
            rel_id: Relationship ID for error messages

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)
        location = f"Relationship {rel_id}"

        # Required fields
        if not rel_params.get('task_id'):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="REL_001",
                message="Successor task ID is required",
                location=location,
                field="task_id"
            ))

        if not rel_params.get('pred_task_id'):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="REL_002",
                message="Predecessor task ID is required",
                location=location,
                field="pred_task_id"
            ))

        # Relationship type validation
        pred_type = rel_params.get('pred_type', '').strip() if rel_params.get('pred_type') else None
        if pred_type and pred_type not in self.VALID_RELATIONSHIP_TYPES:
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="REL_003",
                message=f"Unknown relationship type: {pred_type}",
                location=location,
                field="pred_type",
                value=pred_type
            ))

        # Self-referencing check
        if rel_params.get('task_id') == rel_params.get('pred_task_id'):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="REL_004",
                message="Activity cannot be its own predecessor",
                location=location
            ))

        # Large lag warning
        try:
            lag = parse_float(rel_params.get('lag_hr_cnt'))
            if lag is not None and abs(lag) > 480:  # More than 60 days (480 hours)
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="REL_005",
                    message=f"Large lag value: {lag / 8.0:.1f} days",
                    location=location,
                    field="lag_hr_cnt",
                    value=lag
                ))
        except ValueError:
            pass

        return result

    def validate_project(
        self,
        proj_params: Dict[str, Any],
        proj_id: str = "unknown"
    ) -> ValidationResult:
        """
        Validate project data.

        Args:
            proj_params: Dictionary of project parameters
            proj_id: Project ID for error messages

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult(is_valid=True)
        location = f"Project {proj_id}"

        # Required fields
        if not proj_params.get('proj_id'):
            result.add_issue(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="PROJ_001",
                message="Project ID is required",
                location=location,
                field="proj_id"
            ))

        # Date validation
        try:
            plan_start = parse_datetime(proj_params.get('plan_start_date'), format='%Y-%m-%d')
            plan_end = parse_datetime(proj_params.get('plan_end_date'), format='%Y-%m-%d')

            if plan_start and plan_end and plan_start > plan_end:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="PROJ_002",
                    message="Plan start date is after plan end date",
                    location=location
                ))
        except ValueError:
            pass

        return result


def validate_xer_structure(reader) -> ValidationResult:
    """
    Validate the overall structure and integrity of parsed XER data.

    Args:
        reader: A Reader object with parsed XER data

    Returns:
        ValidationResult with any issues found
    """
    result = ValidationResult(is_valid=True)
    validator = XERValidator()

    # Check for required data
    if not hasattr(reader, 'projects') or len(reader.projects) == 0:
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="XER_001",
            message="No projects found in XER file"
        ))

    if not hasattr(reader, 'activities') or len(reader.activities) == 0:
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="XER_002",
            message="No activities found in XER file"
        ))

    # Validate activities
    if hasattr(reader, 'activities'):
        for activity in reader.activities:
            activity_params = {
                'task_id': getattr(activity, 'task_id', None),
                'proj_id': getattr(activity, 'proj_id', None),
                'status_code': getattr(activity, 'status_code', None),
                'task_type': getattr(activity, 'task_type', None),
                'duration_type': getattr(activity, 'duration_type', None),
                'cstr_type': getattr(activity, 'cstr_type', None),
                'target_start_date': getattr(activity, 'target_start_date', None),
                'target_end_date': getattr(activity, 'target_end_date', None),
                'act_end_date': getattr(activity, 'act_end_date', None),
                'remain_drtn_hr_cnt': getattr(activity, 'remain_drtn_hr_cnt', None),
                'target_drtn_hr_cnt': getattr(activity, 'target_drtn_hr_cnt', None),
            }
            task_code = getattr(activity, 'task_code', 'unknown')
            task_result = validator.validate_task(activity_params, task_code)
            result.merge(task_result)

    # Check for orphan activities (no WBS)
    if hasattr(reader, 'activities'):
        wbs_ids = set()
        if hasattr(reader, 'wbss'):
            wbs_ids = {w.wbs_id for w in reader.wbss if hasattr(w, 'wbs_id')}

        for activity in reader.activities:
            if hasattr(activity, 'wbs_id') and activity.wbs_id not in wbs_ids:
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="XER_010",
                    message=f"Activity references non-existent WBS",
                    location=f"Task {getattr(activity, 'task_code', 'unknown')}",
                    field="wbs_id",
                    value=activity.wbs_id
                ))

    # Check for circular relationships
    if hasattr(reader, 'relations'):
        # Build predecessor graph
        predecessors: Dict[int, Set[int]] = {}
        for rel in reader.relations:
            task_id = getattr(rel, 'task_id', None)
            pred_id = getattr(rel, 'pred_task_id', None)
            if task_id and pred_id:
                if task_id not in predecessors:
                    predecessors[task_id] = set()
                predecessors[task_id].add(pred_id)

        # Simple cycle detection (limited depth)
        def has_cycle(task_id: int, visited: Set[int], depth: int = 0) -> bool:
            if depth > 100:  # Prevent infinite loops
                return False
            if task_id in visited:
                return True
            visited.add(task_id)
            for pred in predecessors.get(task_id, []):
                if has_cycle(pred, visited.copy(), depth + 1):
                    return True
            return False

        for task_id in predecessors:
            if has_cycle(task_id, set()):
                result.add_issue(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="XER_020",
                    message="Circular relationship detected",
                    location=f"Task ID {task_id}"
                ))
                break  # Report only first cycle found

    return result
