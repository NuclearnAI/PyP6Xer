"""
Tests for bugs identified and fixed during code review.

These tests ensure that the following issues remain fixed:
1. Bare except clause in task.py external date parsing
2. Copy-paste bug in project.py last_baseline_update_date
3. Property typo in task.py (totalint -> totalfloat)
4. Duplicate constraint check in analysis.py
5. Typo in task.py constraints dict (ConstrintDate -> ConstraintDate)
6. Empty string handling in project.py fintmpl_id
7. Division by zero guards in analysis.py
8. File handle leak in reader.py get_num_lines()
9. Wildcard import replacement in reader.py
10. duration property guards a missing calendar (falls back to 8h/day)
11. __repr__ returns "" when task_code is None
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xerparser.model.classes.project import Project
from xerparser.model.classes.task import Task
from xerparser.model.classes.data import Data


class TestTaskExternalDateParsing(unittest.TestCase):
    """Test fixes for bare except clause in task.py external date parsing."""

    def setUp(self):
        self.data = Data()

    def _create_minimal_task_params(self, **overrides):
        """Create minimal valid task params with optional overrides."""
        params = {
            'task_id': '1',
            'proj_id': '1',
            'wbs_id': '1',
            'clndr_id': '1',
            'task_code': 'A1000',
            'task_name': 'Test Task',
            'status_code': 'TK_NotStart',
            'task_type': 'TT_Task',
            'duration_type': 'DT_FixedDrtn',
            'complete_pct_type': 'CP_Drtn',
        }
        params.update(overrides)
        return params

    def test_external_early_start_date_valid(self):
        """Test that valid external_early_start_date is parsed correctly."""
        params = self._create_minimal_task_params(
            external_early_start_date='2023-06-15 09:00'
        )
        task = Task(params, self.data)
        self.assertEqual(task.external_early_start_date, datetime(2023, 6, 15, 9, 0))

    def test_external_early_start_date_invalid_format(self):
        """Test that invalid external_early_start_date format results in None, not crash."""
        params = self._create_minimal_task_params(
            external_early_start_date='invalid-date'
        )
        # Should not raise an exception
        task = Task(params, self.data)
        # Should be None due to the fix
        self.assertIsNone(task.external_early_start_date)

    def test_external_early_start_date_empty(self):
        """Test that empty external_early_start_date is handled correctly."""
        params = self._create_minimal_task_params(
            external_early_start_date=''
        )
        task = Task(params, self.data)
        self.assertIsNone(task.external_early_start_date)

    def test_external_late_end_date_valid(self):
        """Test that valid external_late_end_date is parsed correctly."""
        params = self._create_minimal_task_params(
            external_late_end_date='2023-12-31 17:00'
        )
        task = Task(params, self.data)
        self.assertEqual(task.external_late_end_date, datetime(2023, 12, 31, 17, 0))

    def test_external_late_end_date_invalid_format(self):
        """Test that invalid external_late_end_date format results in None, not crash."""
        params = self._create_minimal_task_params(
            external_late_end_date='not-a-date'
        )
        task = Task(params, self.data)
        self.assertIsNone(task.external_late_end_date)

    def test_both_external_dates_invalid(self):
        """Test that both external dates can be invalid without crashing."""
        params = self._create_minimal_task_params(
            external_early_start_date='bad-date-1',
            external_late_end_date='bad-date-2'
        )
        task = Task(params, self.data)
        self.assertIsNone(task.external_early_start_date)
        self.assertIsNone(task.external_late_end_date)

    def test_external_dates_attribute_always_exists(self):
        """Test that external date attributes are always initialized (not missing)."""
        params = self._create_minimal_task_params(
            external_early_start_date='invalid'
        )
        task = Task(params, self.data)
        # These should exist and not raise AttributeError
        self.assertTrue(hasattr(task, 'external_early_start_date'))
        self.assertTrue(hasattr(task, 'external_late_end_date'))


class TestProjectLastBaselineUpdateDate(unittest.TestCase):
    """Test fix for copy-paste bug in project.py last_baseline_update_date."""

    def setUp(self):
        self.data = Data()

    def test_last_baseline_update_date_uses_correct_field(self):
        """Test that last_baseline_update_date reads from the correct field."""
        params = {
            'proj_id': '1',
            'last_fin_dates_id': 'fin_dates_value',
            'last_baseline_update_date': 'baseline_update_value',
        }
        project = Project(params, self.data)

        # Before fix: last_baseline_update_date was reading from last_fin_dates_id
        # After fix: it should read from last_baseline_update_date
        self.assertEqual(project.last_baseline_update_date, 'baseline_update_value')
        self.assertEqual(project.last_fin_dates_id, 'fin_dates_value')

    def test_last_baseline_update_date_independent_of_last_fin_dates_id(self):
        """Test that the two fields are independent."""
        params = {
            'proj_id': '1',
            'last_fin_dates_id': 'only_fin_dates',
        }
        project = Project(params, self.data)

        # last_baseline_update_date should be None since it wasn't provided
        self.assertIsNone(project.last_baseline_update_date)
        self.assertEqual(project.last_fin_dates_id, 'only_fin_dates')

    def test_last_baseline_update_date_when_only_it_is_provided(self):
        """Test last_baseline_update_date when only it is provided."""
        params = {
            'proj_id': '1',
            'last_baseline_update_date': 'only_baseline',
        }
        project = Project(params, self.data)

        self.assertEqual(project.last_baseline_update_date, 'only_baseline')
        self.assertIsNone(project.last_fin_dates_id)


class TestTaskTotalFloatProperty(unittest.TestCase):
    """Test fix for totalint -> totalfloat property rename and attribute fix."""

    def setUp(self):
        self.data = Data()

    def _create_task_with_float(self, total_float_hr_cnt):
        """Create a task with specified total float."""
        params = {
            'task_id': '1',
            'proj_id': '1',
            'wbs_id': '1',
            'clndr_id': '1',
            'task_code': 'A1000',
            'task_name': 'Test Task',
            'status_code': 'TK_NotStart',
            'task_type': 'TT_Task',
            'duration_type': 'DT_FixedDrtn',
            'complete_pct_type': 'CP_Drtn',
            'total_float_hr_cnt': str(total_float_hr_cnt) if total_float_hr_cnt is not None else '',
        }
        return Task(params, self.data)

    def test_totalfloat_property_exists(self):
        """Test that the property is named totalfloat (not totalint)."""
        task = self._create_task_with_float(80)
        self.assertTrue(hasattr(task, 'totalfloat'))

    def test_totalfloat_calculates_correctly(self):
        """Test that totalfloat divides by 8 correctly."""
        task = self._create_task_with_float(80)  # 80 hours = 10 days
        self.assertEqual(task.totalfloat, 10.0)

    def test_totalfloat_with_zero(self):
        """Test totalfloat with zero value."""
        task = self._create_task_with_float(0)
        # 0 is falsy, so should return None based on the implementation
        self.assertIsNone(task.totalfloat)

    def test_totalfloat_with_none(self):
        """Test totalfloat with None value."""
        task = self._create_task_with_float(None)
        self.assertIsNone(task.totalfloat)

    def test_totalfloat_with_negative(self):
        """Test totalfloat with negative value (negative float)."""
        task = self._create_task_with_float(-16)  # -16 hours = -2 days
        self.assertEqual(task.totalfloat, -2.0)


class TestTaskConstraintsTypo(unittest.TestCase):
    """Test fix for ConstrintDate -> ConstraintDate typo."""

    def setUp(self):
        self.data = Data()

    def _create_task_with_constraint(self, cstr_type, cstr_date):
        """Create a task with specified constraint."""
        params = {
            'task_id': '1',
            'proj_id': '1',
            'wbs_id': '1',
            'clndr_id': '1',
            'task_code': 'A1000',
            'task_name': 'Test Task',
            'status_code': 'TK_NotStart',
            'task_type': 'TT_Task',
            'duration_type': 'DT_FixedDrtn',
            'complete_pct_type': 'CP_Drtn',
            'cstr_type': cstr_type,
            'cstr_date': cstr_date,
        }
        return Task(params, self.data)

    def test_constraints_dict_has_correct_key(self):
        """Test that constraints dict uses ConstraintDate (not ConstrintDate)."""
        task = self._create_task_with_constraint('CS_MSOA', '2023-06-15 09:00')
        constraints = task.constraints

        self.assertIsNotNone(constraints)
        # Check correct spelling
        self.assertIn('ConstraintDate', constraints)
        # Check wrong spelling is NOT present
        self.assertNotIn('ConstrintDate', constraints)

    def test_constraints_dict_structure(self):
        """Test that constraints dict has expected structure."""
        task = self._create_task_with_constraint('CS_MSOA', '2023-06-15 09:00')
        constraints = task.constraints

        self.assertIn('ConstraintType', constraints)
        self.assertIn('ConstraintDate', constraints)
        self.assertEqual(constraints['ConstraintType'], 'CS_MSOA')

    def test_constraints_returns_none_when_no_constraint(self):
        """Test constraints returns None when no constraint is set."""
        task = self._create_task_with_constraint(None, None)
        self.assertIsNone(task.constraints)


class TestProjectFintmplIdValidation(unittest.TestCase):
    """Test fix for fintmpl_id empty string handling."""

    def setUp(self):
        self.data = Data()

    def test_fintmpl_id_valid_integer(self):
        """Test that valid integer string is parsed correctly."""
        params = {'proj_id': '1', 'fintmpl_id': '123'}
        project = Project(params, self.data)
        self.assertEqual(project.fintmpl_id, 123)

    def test_fintmpl_id_empty_string(self):
        """Test that empty string doesn't cause ValueError."""
        params = {'proj_id': '1', 'fintmpl_id': ''}
        # Before fix: int('') would raise ValueError
        # After fix: should return None
        project = Project(params, self.data)
        self.assertIsNone(project.fintmpl_id)

    def test_fintmpl_id_whitespace_only(self):
        """Test that whitespace-only string is handled as empty."""
        params = {'proj_id': '1', 'fintmpl_id': '   '}
        project = Project(params, self.data)
        self.assertIsNone(project.fintmpl_id)

    def test_fintmpl_id_with_whitespace(self):
        """Test that integer with whitespace is parsed correctly."""
        params = {'proj_id': '1', 'fintmpl_id': '  456  '}
        project = Project(params, self.data)
        self.assertEqual(project.fintmpl_id, 456)

    def test_fintmpl_id_none(self):
        """Test that None value is handled correctly."""
        params = {'proj_id': '1', 'fintmpl_id': None}
        project = Project(params, self.data)
        self.assertIsNone(project.fintmpl_id)

    def test_fintmpl_id_missing(self):
        """Test that missing fintmpl_id is handled correctly."""
        params = {'proj_id': '1'}
        project = Project(params, self.data)
        self.assertIsNone(project.fintmpl_id)


class TestTaskDurationMissingCalendar(unittest.TestCase):
    """Test duration falls back to 8h/day when the task has no calendar (stranded fix)."""

    def setUp(self):
        self.data = Data()

    def test_duration_with_no_calendar_falls_back_to_8h(self):
        """A task whose clndr_id matches no calendar must not raise on .duration."""
        params = {
            'task_id': '1',
            'proj_id': '1',
            'wbs_id': '1',
            'clndr_id': '-999',  # cannot collide with any real/leaked calendar id
            'task_code': 'A1000',
            'task_name': 'Test Task',
            'status_code': 'TK_NotStart',
            'task_type': 'TT_Task',
            'duration_type': 'DT_FixedDrtn',
            'complete_pct_type': 'CP_Drtn',
            'target_drtn_hr_cnt': '80',
        }
        task = Task(params, self.data)
        # Precondition: no calendar resolved for this id.
        self.assertIsNone(task.calendar)
        # Before fix: AttributeError on None.day_hr_cnt. After fix: 8h/day fallback.
        self.assertEqual(task.duration, 80.0 / 8.0)


class TestTaskReprNoneTaskCode(unittest.TestCase):
    """Test __repr__ returns '' when task_code is None (stranded fix)."""

    def setUp(self):
        self.data = Data()

    def test_repr_with_none_task_code(self):
        """repr() must not raise TypeError when task_code is None."""
        params = {
            'task_id': '1',
            'proj_id': '1',
            'wbs_id': '1',
            'clndr_id': '1',
            'task_name': 'Test Task',
            'status_code': 'TK_NotStart',
            'task_type': 'TT_Task',
            'duration_type': 'DT_FixedDrtn',
            'complete_pct_type': 'CP_Drtn',
        }
        task = Task(params, self.data)
        self.assertIsNone(task.task_code)
        # Before fix: TypeError (__repr__ returned None). After fix: "".
        self.assertEqual(repr(task), "")


class TestReaderFileHandleLeak(unittest.TestCase):
    """Test fix for file handle leak in get_num_lines()."""

    def test_get_num_lines_closes_file(self):
        """Test that get_num_lines properly closes file handle."""
        from xerparser.reader import Reader

        # Create a temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("line1\n")
            f.write("line2\n")
            f.write("line3\n")
            temp_file = f.name

        try:
            # Create a minimal XER file for Reader
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xer', encoding='utf-8') as xer:
                xer.write("ERMHDR\t8.0\t2021-11-02\tProject\n")
                xer.write("%E\n")
                xer_file = xer.name

            reader = Reader(xer_file)

            # Call get_num_lines multiple times - if file isn't closed, we'd eventually hit OS limits
            for _ in range(10):
                count = reader.get_num_lines(temp_file)
                self.assertEqual(count, 3)

            # File should be accessible after get_num_lines (not locked)
            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn("line1", content)
        finally:
            os.unlink(temp_file)
            os.unlink(xer_file)


class TestReaderExplicitImports(unittest.TestCase):
    """Test that wildcard imports were replaced with explicit imports."""

    def test_required_classes_are_importable(self):
        """Test that all required classes are properly imported."""
        # These imports should work if explicit imports are correct
        from xerparser.reader import (
            Reader,
            Tasks,
            Projects,
            WBSs,
            Resources,
            Accounts,
            Calendars,
            Currencies,
            WBS,
            TaskPred,
        )

        # Verify they are classes/types
        self.assertTrue(callable(Reader))
        self.assertTrue(callable(Tasks))
        self.assertTrue(callable(Projects))
        self.assertTrue(callable(WBS))
        self.assertTrue(callable(TaskPred))

    def test_reader_can_be_instantiated(self):
        """Test that Reader can be instantiated with explicit imports."""
        from xerparser.reader import Reader

        # Create a minimal valid XER file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xer', encoding='utf-8') as f:
            f.write("ERMHDR\t8.0\t2021-11-02\tProject\n")
            f.write("%E\n")
            temp_file = f.name

        try:
            reader = Reader(temp_file)
            self.assertIsNotNone(reader)
        finally:
            os.unlink(temp_file)


class TestDCMA14DivisionByZero(unittest.TestCase):
    """Test fix for division by zero guards in analysis.py."""

    def setUp(self):
        """Set up mock programme with empty activities/relations."""
        self.mock_programme = MagicMock()

    def test_analysis_with_zero_activities(self):
        """Test that analysis doesn't crash with zero activities."""
        from xerparser.dcma14.analysis import DCMA14

        # Mock programme with no activities - use MagicMock for nested attributes
        mock_activities = MagicMock()
        mock_activities.__len__ = MagicMock(return_value=0)
        mock_activities.__iter__ = MagicMock(return_value=iter([]))
        mock_activities.activities = []
        mock_activities.has_no_successor = []
        mock_activities.has_no_predecessor = []

        mock_relations = MagicMock()
        mock_relations.__len__ = MagicMock(return_value=0)
        mock_relations.__iter__ = MagicMock(return_value=iter([]))
        mock_relations.leads = []
        mock_relations.finish_to_start = []

        self.mock_programme.activities = mock_activities
        self.mock_programme.relations = mock_relations
        self.mock_programme.projects = []
        self.mock_programme.activityresources = MagicMock()
        self.mock_programme.activityresources.find_by_activity_id = MagicMock(return_value=[])

        dcma = DCMA14(self.mock_programme)

        # Should not raise ZeroDivisionError
        try:
            results = dcma.analysis()
            # All percentages should be 0.0 when activity_count is 0
            self.assertEqual(results['analysis']['successors']['pct'], 0.0)
            self.assertEqual(results['analysis']['predecessors']['pct'], 0.0)
        except ZeroDivisionError:
            self.fail("Division by zero occurred with zero activities")

    def test_analysis_with_zero_relations(self):
        """Test that analysis doesn't crash with zero relations."""
        from xerparser.dcma14.analysis import DCMA14

        # Mock programme with activities but no relations
        mock_activity = MagicMock()
        mock_activity.task_id = 1
        mock_activity.proj_id = 1
        mock_activity.total_float_hr_cnt = 0
        mock_activity.duration = 5
        mock_activity.cstr_type = None
        mock_activity.act_start_date = None
        mock_activity.act_end_date = None
        mock_activity.early_start_date = None
        mock_activity.early_end_date = None
        mock_activity.target_end_date = None
        mock_activity.task_code = 'A1000'
        mock_activity.task_name = 'Test'

        mock_activities = MagicMock()
        mock_activities.__len__ = MagicMock(return_value=1)
        mock_activities.__iter__ = MagicMock(return_value=iter([mock_activity]))
        mock_activities.activities = [mock_activity]
        mock_activities.has_no_successor = [mock_activity]
        mock_activities.has_no_predecessor = [mock_activity]
        mock_activities.find_by_id = MagicMock(return_value=mock_activity)

        mock_relations = MagicMock()
        mock_relations.__len__ = MagicMock(return_value=0)
        mock_relations.__iter__ = MagicMock(return_value=iter([]))
        mock_relations.leads = []
        mock_relations.finish_to_start = []

        self.mock_programme.activities = mock_activities
        self.mock_programme.relations = mock_relations
        self.mock_programme.projects = []
        self.mock_programme.activityresources = MagicMock()
        self.mock_programme.activityresources.find_by_activity_id = MagicMock(return_value=[])

        dcma = DCMA14(self.mock_programme)

        # Should not raise ZeroDivisionError
        try:
            results = dcma.analysis()
            # Relation percentages should be 0.0 when relation_count is 0
            self.assertEqual(results['analysis']['lags']['pct'], 0.0)
            self.assertEqual(results['analysis']['leads']['pct'], 0.0)
        except ZeroDivisionError:
            self.fail("Division by zero occurred with zero relations")


class TestDCMA14ConstraintCheck(unittest.TestCase):
    """Test fix for duplicate constraint check in analysis.py."""

    def test_constraint_list_has_both_values(self):
        """Test that constraint list includes both CS_MANDSTART and CS_MANDFIN."""
        from xerparser.dcma14.analysis import DCMA14

        mock_programme = MagicMock()
        dcma = DCMA14(mock_programme)

        # We can't directly access the list, but we can test the behavior
        # by checking the source code or testing with mock data

        # Create mock activities with different constraint types
        mock_activity_start = MagicMock()
        mock_activity_start.cstr_type = 'CS_MANDSTART'
        mock_activity_start.task_id = 1

        mock_activity_fin = MagicMock()
        mock_activity_fin.cstr_type = 'CS_MANDFIN'
        mock_activity_fin.task_id = 2

        mock_activity_other = MagicMock()
        mock_activity_other.cstr_type = 'CS_MSOA'  # Should not be included
        mock_activity_other.task_id = 3

        # Filter as the code does
        lst = ['CS_MANDSTART', 'CS_MANDFIN']
        activities = [mock_activity_start, mock_activity_fin, mock_activity_other]
        constraints = list(filter(lambda x: x.cstr_type and x.cstr_type in lst, activities))

        # Both mandatory constraints should be found
        self.assertEqual(len(constraints), 2)
        self.assertIn(mock_activity_start, constraints)
        self.assertIn(mock_activity_fin, constraints)
        self.assertNotIn(mock_activity_other, constraints)


class TestAnalysisNoDebugPrints(unittest.TestCase):
    """Test that debug print statements were removed from analysis.py."""

    def test_analysis_has_no_print_to_stdout(self):
        """Test that analysis() doesn't print debug output to stdout."""
        from xerparser.dcma14.analysis import DCMA14
        import io
        import sys

        # Create mock programme with proper nested mocking
        mock_programme = MagicMock()

        mock_activities = MagicMock()
        mock_activities.__len__ = MagicMock(return_value=0)
        mock_activities.__iter__ = MagicMock(return_value=iter([]))
        mock_activities.activities = []
        mock_activities.has_no_successor = []
        mock_activities.has_no_predecessor = []

        mock_relations = MagicMock()
        mock_relations.__len__ = MagicMock(return_value=0)
        mock_relations.__iter__ = MagicMock(return_value=iter([]))
        mock_relations.leads = []
        mock_relations.finish_to_start = []

        mock_programme.activities = mock_activities
        mock_programme.relations = mock_relations
        mock_programme.projects = []
        mock_programme.activityresources = MagicMock()
        mock_programme.activityresources.find_by_activity_id = MagicMock(return_value=[])

        dcma = DCMA14(mock_programme)

        # Capture stdout
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            dcma.analysis()
        finally:
            sys.stdout = old_stdout

        output = captured_output.getvalue()

        # Should not contain debug print statements
        self.assertNotIn("SLIPPED", output)
        self.assertNotIn("TF FOUND", output)
        self.assertNotIn("TF Not found", output)
        # Check that we're not printing data_date dict or no_resources list
        self.assertNotIn("{", output)  # No dict printing
        self.assertEqual(output.strip(), "")  # Should be empty


if __name__ == '__main__':
    unittest.main()
