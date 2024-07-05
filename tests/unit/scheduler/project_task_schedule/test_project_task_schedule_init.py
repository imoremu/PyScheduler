import unittest
from unittest.mock import MagicMock
import pandas as pd

from scheduler.project_scheduler_constants import (
    TASK_ID, TASK_PRIORITY, TASK_ESTIMATION, TASK_RESOURCES_MAX,
    TASK_RESTRICTION, TASK_REMAINING, TASK_GOAL
)

from scheduler.project_task_scheduler import TaskManager

class TestTaskManagerInitialization(unittest.TestCase):
    """Test cases focused on validating TaskManager initialization."""

    def setUp(self):
        self.tasks_df = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2'],
            TASK_GOAL: ['Task1', 'Task2'],
            TASK_PRIORITY: [1, 2],
            TASK_ESTIMATION: [5, 10],
            TASK_RESOURCES_MAX: [2, 2],
            TASK_RESTRICTION: [None, None],
            TASK_REMAINING: [5, 10],
        })        

        self.resource_manager = MagicMock()
                        
    def test_no_missing_columns(self):
        TaskManager(self.tasks_df, self.resource_manager)       

    def test_missing_columns(self):
        """Test TaskManager initialization with missing columns."""
        with self.assertRaises(ValueError):
            TaskManager(self.tasks_df.drop([TASK_PRIORITY], axis=1), self.resource_manager)

        with self.assertRaises(ValueError):
            TaskManager(self.tasks_df.drop([TASK_ID], axis=1), self.resource_manager)

        with self.assertRaises(ValueError):
            TaskManager(self.tasks_df.drop([TASK_REMAINING], axis=1), self.resource_manager)

        with self.assertRaises(ValueError):
            self.resource_manager.responsible_attr_names = ['RESPONSIBLE']            
            TaskManager(self.tasks_df, self.resource_manager)

    def test_initialize_task_resources_max_empty(self):
        # Setup a DataFrame with empty TASK_RESOURCES_MAX values
        tasks_df_empty_resources_max = pd.DataFrame({
            TASK_ID: [1],
            TASK_GOAL: ['Task1'],
            "Team": ["T1"],            
            TASK_PRIORITY: [1],
            TASK_REMAINING: [10],
            TASK_RESOURCES_MAX: [''],            
        })

        task_manager = TaskManager(tasks_df_empty_resources_max, self.resource_manager)

        expected_resources_max = float('inf')
        self.assertEqual(task_manager.tasks_df.iloc[0][TASK_RESOURCES_MAX], expected_resources_max)

    def test_initialize_task_resources_max_none(self):
        # Setup a DataFrame with empty TASK_RESOURCES_MAX values
        tasks_df_empty_resources_max = pd.DataFrame({
            TASK_ID: [1],
            TASK_GOAL: ['Task1'],
            "Team": ["T1"],            
            TASK_PRIORITY: [1],
            TASK_REMAINING: [10],
            TASK_RESOURCES_MAX: [None],            
        })

        task_manager = TaskManager(tasks_df_empty_resources_max, self.resource_manager)

        expected_resources_max = float('inf')
        self.assertEqual(task_manager.tasks_df.iloc[0][TASK_RESOURCES_MAX], expected_resources_max)

    def test_initialize_task_resources_max_missing(self):
        # Setup a DataFrame without TASK_RESOURCES_MAX column
        tasks_df_missing_resources_max = pd.DataFrame({
            TASK_ID: [1, 2, 3],
            TASK_GOAL: ['Task1', 'Task2', 'Task3'],
            "Team": ["T1", "T2", "T3"],            
            TASK_PRIORITY: [1, 2, 3], # Important to keep it ordered because TaskManager order by priority
            TASK_REMAINING: [10, 5, 8],
            TASK_RESTRICTION: [None, None, None],
        })
        
        task_manager = TaskManager(tasks_df_missing_resources_max, self.resource_manager)

        expected_resources_max = pd.Series([float('inf'), float('inf'), float('inf')], name=TASK_RESOURCES_MAX)
        pd.testing.assert_series_equal(task_manager.tasks_df[TASK_RESOURCES_MAX], expected_resources_max)


    def test_initialize_task_restriction_empty(self):
        # Setup a DataFrame with empty TASK_RESTRICTION values
        tasks_df_empty_restriction = pd.DataFrame({
            TASK_ID: [1, 2, 3],
            TASK_GOAL: ['Task1', 'Task2', 'Task3'],
            "Team": ["T1", "T2", "T3"],            
            TASK_PRIORITY: [1, 2, 3], # Important to keep it ordered because TaskManager order by priority
            TASK_REMAINING: [10, 5, 8],
            TASK_RESOURCES_MAX: [5, 5, 5],
            TASK_RESTRICTION: ['', "T3", None],  # Empty values
        })

        task_manager = TaskManager(tasks_df_empty_restriction, self.resource_manager)

        expected_restriction = pd.Series([None, "T3", None], name=TASK_RESTRICTION)
        pd.testing.assert_series_equal(task_manager.tasks_df[TASK_RESTRICTION], expected_restriction)

    def test_initialize_task_restriction_missing(self):
        # Setup a DataFrame without TASK_RESTRICTION column
        tasks_df_missing_restriction = pd.DataFrame({
            TASK_ID: [1, 2, 3],
            TASK_GOAL: ['Task1', 'Task2', 'Task3'],
            "Team": ["T1", "T2", "T3"],            
            TASK_PRIORITY: [1, 2, 3], # Important to keep it ordered because TaskManager order by priority
            TASK_REMAINING: [10, 5, 8],
            TASK_RESOURCES_MAX: [5, 5, 5],
        })

        task_manager = TaskManager(tasks_df_missing_restriction, self.resource_manager)

        expected_restriction = pd.Series([None, None, None], name=TASK_RESTRICTION)
        pd.testing.assert_series_equal(task_manager.tasks_df[TASK_RESTRICTION], expected_restriction)


if __name__ == '__main__':

    unittest.main()