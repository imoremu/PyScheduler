import unittest
from unittest.mock import MagicMock, patch

import pandas as pd
from datetime import datetime

from utils.app_config import AppConfig
from utils.util_constants import CONF_DAYFIRST
AppConfig()[CONF_DAYFIRST] = True

from utils.date_utils import safe_to_datetime

from scheduler.project_scheduler_constants import (
    TASK_ID, TASK_PRIORITY, TASK_ESTIMATION, TASK_RESOURCES_MAX,
    TASK_RESTRICTION, TASK_REMAINING, TASK_START_DATE, TASK_END_DATE
)

from scheduler.project_task_scheduler import TaskManager


class TestTaskFilterByRestriction(unittest.TestCase):
    """Test filtering tasks by different types of restrictions."""

    def setUp(self):
        AppConfig()[CONF_DAYFIRST] = True

    def test_restriction_by_id(self):
        """Test tasks filtered by restriction using task ID."""
       
        tasks_df = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2', 'Task3'],
            TASK_PRIORITY: [1, 2, 1],
            TASK_ESTIMATION: [5, 8, 3],
            TASK_RESOURCES_MAX: [2, 2, 1],
            TASK_RESTRICTION: [None, 'Task1', None],
            TASK_REMAINING: [5, 8, 3],
            TASK_START_DATE: [None, None, None],
            TASK_END_DATE: [None, None, None],
            'Team': ['Team A', 'Team A', 'Team B'],
            'Project': ['Project X', 'Project Y', "*"]
            })

        completed_tasks = []

        filtered_tasks_df = TaskManager.filter_tasks_by_restriction(tasks_df, completed_tasks, datetime.today().date())        
        ids = set(filtered_tasks_df[TASK_ID]) 
        self.assertEqual(ids, set(['Task1', 'Task3']))  # Task 2 is filtered as Task 1 (restriction) is not completed

        completed_tasks = ['Task1']
        filtered_tasks_df = TaskManager.filter_tasks_by_restriction(tasks_df, completed_tasks, datetime.today().date())        
        
        ids = set(filtered_tasks_df[TASK_ID]) 
        self.assertEqual(ids, set(['Task2', 'Task3']))  # Task 1 is filtered as it's completed. Task 2 remains as Task 1 (restriction) has finished

    def test_restriction_by_date(self):
        """Test tasks filtered by restriction using a date string."""
        tasks_df = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2', 'Task3'],
            TASK_PRIORITY: [1, 2, 1],
            TASK_ESTIMATION: [5, 8, 3],
            TASK_RESOURCES_MAX: [2, 2, 1],
            TASK_RESTRICTION: [None, None, safe_to_datetime("01/05/2025")],
            TASK_REMAINING: [5, 8, 3],
            TASK_START_DATE: [None, None, None],
            TASK_END_DATE: [None, None, None],
            'Team': ['Team A', 'Team A', 'Team B'],
            'Project': ['Project X', 'Project Y', "*"]
        })
        
        completed_tasks = []
        filtered_tasks_df = TaskManager.filter_tasks_by_restriction(tasks_df, completed_tasks, "01/04/2025")

        # Task3 has a future date restriction, so only Task1 and Task2 remain
        ids = set(filtered_tasks_df[TASK_ID]) 
        self.assertEqual(ids, set(['Task1', 'Task2']))

        completed_tasks = []
        filtered_tasks_df = TaskManager.filter_tasks_by_restriction(tasks_df, completed_tasks, "01/06/2025")

        # Task3 has a past date restriction, so all tasks remain
        self.assertEqual(len(filtered_tasks_df), 3)

if __name__ == '__main__':
    unittest.main()
