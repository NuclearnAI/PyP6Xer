"""
Tests for the validation module.

These tests ensure that the validation utilities work correctly for:
1. Type conversion helpers
2. XER data validation
3. Schedule integrity checks
"""

import unittest
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xerparser.validation import (
    parse_int,
    parse_float,
    parse_datetime,
    parse_string,
    parse_bool,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    XERValidator,
    validate_xer_structure,
)


class TestParseInt(unittest.TestCase):
    """Tests for parse_int function."""

    def test_valid_integer(self):
        """Test parsing a valid integer string."""
        self.assertEqual(parse_int("123"), 123)
        self.assertEqual(parse_int("  456  "), 456)
        self.assertEqual(parse_int("-789"), -789)

    def test_empty_string(self):
        """Test handling of empty strings."""
        self.assertIsNone(parse_int(""))
        self.assertIsNone(parse_int("   "))
        self.assertIsNone(parse_int(None))

    def test_with_default(self):
        """Test parsing with default value."""
        self.assertEqual(parse_int("invalid", default=0), 0)
        self.assertEqual(parse_int("", default=42), 42)

    def test_invalid_raises_without_default(self):
        """Test that invalid input raises ValueError without default."""
        with self.assertRaises(ValueError):
            parse_int("not_a_number", allow_empty=False)

    def test_allow_empty_false(self):
        """Test that empty input raises ValueError when not allowed."""
        with self.assertRaises(ValueError):
            parse_int("", allow_empty=False)


class TestParseFloat(unittest.TestCase):
    """Tests for parse_float function."""

    def test_valid_float(self):
        """Test parsing valid float strings."""
        self.assertEqual(parse_float("123.45"), 123.45)
        self.assertEqual(parse_float("  67.89  "), 67.89)
        self.assertEqual(parse_float("-12.34"), -12.34)

    def test_integer_as_float(self):
        """Test parsing integer strings as floats."""
        self.assertEqual(parse_float("100"), 100.0)

    def test_empty_string(self):
        """Test handling of empty strings."""
        self.assertIsNone(parse_float(""))
        self.assertIsNone(parse_float(None))

    def test_with_default(self):
        """Test parsing with default value."""
        self.assertEqual(parse_float("invalid", default=0.0), 0.0)


class TestParseDatetime(unittest.TestCase):
    """Tests for parse_datetime function."""

    def test_valid_datetime(self):
        """Test parsing valid datetime strings."""
        result = parse_datetime("2023-06-15 09:30")
        self.assertEqual(result, datetime(2023, 6, 15, 9, 30))

    def test_empty_string(self):
        """Test handling of empty strings."""
        self.assertIsNone(parse_datetime(""))
        self.assertIsNone(parse_datetime(None))

    def test_invalid_format(self):
        """Test handling of invalid format."""
        self.assertIsNone(parse_datetime("invalid", default=None))

    def test_with_default(self):
        """Test parsing with default value."""
        default = datetime(2020, 1, 1)
        result = parse_datetime("invalid", default=default)
        self.assertEqual(result, default)

    def test_custom_format(self):
        """Test parsing with custom format."""
        result = parse_datetime("15/06/2023", format="%d/%m/%Y")
        self.assertEqual(result, datetime(2023, 6, 15))


class TestParseString(unittest.TestCase):
    """Tests for parse_string function."""

    def test_valid_string(self):
        """Test parsing valid strings."""
        self.assertEqual(parse_string("hello"), "hello")
        self.assertEqual(parse_string("  hello  "), "hello")

    def test_no_strip(self):
        """Test parsing without stripping."""
        self.assertEqual(parse_string("  hello  ", strip=False), "  hello  ")

    def test_empty_string(self):
        """Test handling of empty strings."""
        self.assertIsNone(parse_string(""))
        self.assertIsNone(parse_string("   "))

    def test_with_default(self):
        """Test parsing with default value."""
        self.assertEqual(parse_string("", default="default"), "default")

    def test_max_length(self):
        """Test max length validation."""
        with self.assertRaises(ValueError):
            parse_string("long string", max_length=5)


class TestParseBool(unittest.TestCase):
    """Tests for parse_bool function."""

    def test_true_values(self):
        """Test parsing true values."""
        for val in ['Y', 'y', 'yes', 'Yes', 'YES', 'true', 'True', '1']:
            self.assertTrue(parse_bool(val), f"Expected True for '{val}'")

    def test_false_values(self):
        """Test parsing false values."""
        for val in ['N', 'n', 'no', 'No', 'NO', 'false', 'False', '0']:
            self.assertFalse(parse_bool(val), f"Expected False for '{val}'")

    def test_empty_string(self):
        """Test handling of empty strings."""
        self.assertIsNone(parse_bool(""))
        self.assertIsNone(parse_bool(None))

    def test_with_default(self):
        """Test parsing with default value."""
        self.assertTrue(parse_bool("", default=True))
        self.assertFalse(parse_bool("unknown", default=False))


class TestValidationIssue(unittest.TestCase):
    """Tests for ValidationIssue class."""

    def test_issue_creation(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="TEST_001",
            message="Test error",
            location="Test location",
            field="test_field"
        )
        self.assertEqual(issue.severity, ValidationSeverity.ERROR)
        self.assertEqual(issue.code, "TEST_001")
        self.assertEqual(issue.message, "Test error")

    def test_issue_str(self):
        """Test string representation of issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="WARN_001",
            message="Test warning"
        )
        str_repr = str(issue)
        self.assertIn("WARNING", str_repr)
        self.assertIn("WARN_001", str_repr)
        self.assertIn("Test warning", str_repr)


class TestValidationResult(unittest.TestCase):
    """Tests for ValidationResult class."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)

    def test_add_warning(self):
        """Test adding a warning doesn't invalidate result."""
        result = ValidationResult(is_valid=True)
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="WARN_001",
            message="Warning"
        ))
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 1)

    def test_add_error(self):
        """Test adding an error invalidates result."""
        result = ValidationResult(is_valid=True)
        result.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="ERR_001",
            message="Error"
        ))
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)

    def test_merge_results(self):
        """Test merging two validation results."""
        result1 = ValidationResult(is_valid=True)
        result1.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            code="WARN_001",
            message="Warning 1"
        ))

        result2 = ValidationResult(is_valid=True)
        result2.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="ERR_001",
            message="Error 1"
        ))

        result1.merge(result2)
        self.assertFalse(result1.is_valid)
        self.assertEqual(len(result1.issues), 2)


class TestXERValidator(unittest.TestCase):
    """Tests for XERValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = XERValidator()

    def test_validate_task_valid(self):
        """Test validating a valid task."""
        params = {
            'task_id': '1',
            'proj_id': '100',
            'status_code': 'TK_NotStart',
            'task_type': 'TT_Task',
            'duration_type': 'DT_FixedDrtn',
        }
        result = self.validator.validate_task(params, 'A1000')
        self.assertTrue(result.is_valid)

    def test_validate_task_missing_id(self):
        """Test validating a task with missing ID."""
        params = {
            'proj_id': '100',
        }
        result = self.validator.validate_task(params, 'A1000')
        self.assertFalse(result.is_valid)
        self.assertTrue(any(e.code == 'TASK_001' for e in result.errors))

    def test_validate_task_invalid_status(self):
        """Test validating a task with invalid status code."""
        params = {
            'task_id': '1',
            'proj_id': '100',
            'status_code': 'INVALID_STATUS',
        }
        result = self.validator.validate_task(params, 'A1000')
        self.assertTrue(any(w.code == 'TASK_003' for w in result.warnings))

    def test_validate_task_negative_duration(self):
        """Test validating a task with negative duration."""
        params = {
            'task_id': '1',
            'proj_id': '100',
            'remain_drtn_hr_cnt': '-10',
        }
        result = self.validator.validate_task(params, 'A1000')
        self.assertTrue(any(e.code == 'TASK_020' for e in result.errors))

    def test_validate_relationship_valid(self):
        """Test validating a valid relationship."""
        params = {
            'task_pred_id': '1',
            'task_id': '100',
            'pred_task_id': '200',
            'pred_type': 'PR_FS',
            'lag_hr_cnt': '8',
        }
        result = self.validator.validate_relationship(params, 'REL001')
        self.assertTrue(result.is_valid)

    def test_validate_relationship_self_reference(self):
        """Test validating a self-referencing relationship."""
        params = {
            'task_pred_id': '1',
            'task_id': '100',
            'pred_task_id': '100',
            'pred_type': 'PR_FS',
        }
        result = self.validator.validate_relationship(params, 'REL001')
        self.assertTrue(any(e.code == 'REL_004' for e in result.errors))

    def test_validate_relationship_large_lag(self):
        """Test validating a relationship with large lag."""
        params = {
            'task_pred_id': '1',
            'task_id': '100',
            'pred_task_id': '200',
            'pred_type': 'PR_FS',
            'lag_hr_cnt': '1000',  # > 60 days
        }
        result = self.validator.validate_relationship(params, 'REL001')
        self.assertTrue(any(w.code == 'REL_005' for w in result.warnings))


class TestValidateXERStructure(unittest.TestCase):
    """Tests for validate_xer_structure function."""

    def test_empty_reader(self):
        """Test validating an empty reader."""
        mock_reader = MagicMock()
        mock_reader.projects = []
        mock_reader.activities = []

        result = validate_xer_structure(mock_reader)
        self.assertTrue(any(i.code == 'XER_001' for i in result.issues))
        self.assertTrue(any(i.code == 'XER_002' for i in result.issues))

    def test_orphan_activity_detection(self):
        """Test detection of activities with non-existent WBS."""
        mock_reader = MagicMock()
        mock_reader.projects = [MagicMock(proj_id=1)]

        mock_activity = MagicMock()
        mock_activity.task_id = 1
        mock_activity.task_code = 'A1000'
        mock_activity.proj_id = 1
        mock_activity.wbs_id = 999  # Non-existent WBS
        mock_activity.status_code = 'TK_NotStart'
        mock_activity.task_type = 'TT_Task'
        mock_activity.duration_type = 'DT_FixedDrtn'
        mock_activity.cstr_type = None
        mock_activity.target_start_date = None
        mock_activity.target_end_date = None
        mock_activity.act_end_date = None
        mock_activity.remain_drtn_hr_cnt = 8
        mock_activity.target_drtn_hr_cnt = 8

        mock_reader.activities = [mock_activity]

        mock_wbs = MagicMock()
        mock_wbs.wbs_id = 1
        mock_reader.wbss = [mock_wbs]

        mock_reader.relations = []

        result = validate_xer_structure(mock_reader)
        self.assertTrue(any(i.code == 'XER_010' for i in result.issues))


class TestValidationSeverity(unittest.TestCase):
    """Tests for ValidationSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        self.assertEqual(ValidationSeverity.ERROR.value, "error")
        self.assertEqual(ValidationSeverity.WARNING.value, "warning")
        self.assertEqual(ValidationSeverity.INFO.value, "info")


if __name__ == '__main__':
    unittest.main()
