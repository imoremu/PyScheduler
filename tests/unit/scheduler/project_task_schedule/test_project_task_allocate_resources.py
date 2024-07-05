import datetime
import unittest
from unittest.mock import MagicMock

import pandas as pd

from utils.app_config import AppConfig
from utils.util_constants import CONF_DAYFIRST, CONF_HOLIDAYS

AppConfig()[CONF_DAYFIRST] = True

from scheduler.project_scheduler_constants import (TASK_GOAL, TASK_ID, TASK_PRIORITY, TASK_RESOURCES_MAX, 
                                                   TASK_RESTRICTION, TASK_REMAINING, TASK_START_DATE, TASK_END_DATE)

from scheduler.project_task_scheduler import TaskManager

class TestTaskAllocateResources(unittest.TestCase):
    def setUp(self):

        self.tasks_df = pd.DataFrame({
            TASK_ID: ['Task1'],
            TASK_GOAL: ['Goal1'],
            TASK_PRIORITY: [1],
            TASK_REMAINING: [10],
            TASK_RESOURCES_MAX: [3],
            TASK_RESTRICTION: [None],
            'Team': ['TeamA'],
            'Project': ['Project1']
        })


    def test_allocate_resources_basic(self):
        """Test the basic allocation for a specified task."""        
        task = self.tasks_df.iloc[0]
        original_remaining = task[TASK_REMAINING]
        resources_allocated = 2

        TaskManager.update_task_attributes(task, resources_allocated, '12/10/2024')

        self.assertEqual(task[TASK_REMAINING], original_remaining - resources_allocated)
        self.assertEqual(task[TASK_START_DATE], '12/10/2024')

    def test_allocate_resources_start_date_set_only_once(self):
        """Test that the start date is set only once and does not change on subsequent allocations."""
        task = self.tasks_df.iloc[0]
        # Simulate first allocation
        TaskManager.update_task_attributes(task, 1, '11/10/2024')
        first_start_date = task[TASK_START_DATE]

        # Simulate second allocation on a different date
        TaskManager.update_task_attributes(task, 1, '18/10/2024')

        second_start_date = task[TASK_START_DATE]

        self.assertEqual(second_start_date, '11/10/2024')        
        self.assertEqual(first_start_date, second_start_date)

    def test_allocate_resources_end_date_set_when_task_not_complete(self):
        """Test that the end date is set when the task is completed."""
        task = self.tasks_df.iloc[0]
                
        TaskManager.update_task_attributes(task, task[TASK_REMAINING] / 2, '13/10/2024')
        
        self.assertNotIn(TASK_END_DATE, task.index, "END_DATE column should not have been created")


    def test_allocate_resources_end_date_set_when_task_completes(self):
        """Test that the end date is set when the task is completed."""
        task = self.tasks_df.iloc[0]
                
        TaskManager.update_task_attributes(task, task[TASK_REMAINING], '13/10/2024')
        
        self.assertEqual(task[TASK_END_DATE], '13/10/2024')
       
        TaskManager.update_task_attributes(task, 0, '14/10/2024')

        self.assertEqual(task[TASK_END_DATE], '13/10/2024')
        
    def test_allocate_resources_resources_bigger_than_remaining(self):
        """Test the handling of incorrect parameters."""
        task = self.tasks_df.iloc[0]
                
        TaskManager.update_task_attributes(task, task[TASK_REMAINING] + 1, '11/10/2024')            
        self.assertEqual(task[TASK_REMAINING], 0)
        
    def test_allocate_resources_used_resources_updated(self):
        used_resources_manager = MagicMock()
        tasks_manager = TaskManager(self.tasks_df, used_resources_manager)

        task = self.tasks_df.iloc[0]

        tasks_manager.allocate_resources(task, 2, "24/12/2024")

        used_resources_manager.update_goal_resources.assert_called_once_with("24/12/2024", 2 / 5, **task)

    def test_calculate_end_date_with_block(self):
        holidays = [datetime.date(2024, 12, 25)]
        start_date = datetime.date(2024, 12, 20)  # Friday
        block_days = 3
        expected_end_date = datetime.date(2024, 12, 26)  # The next Thursday (skipping weekend and Christmas)

        result = TaskManager.calculate_end_date_with_block(start_date, block_days, holidays)
        self.assertEqual(result, expected_end_date)

    def test_update_task_attributes_with_block_days(self):
        holidays = [datetime.date(2024, 12, 25)]

        AppConfig()[CONF_HOLIDAYS] = holidays
        
        task = pd.Series({
            TASK_ID: 'Task1',
            TASK_REMAINING: 5,
            TASK_START_DATE: None,
            TASK_END_DATE: None,
            'Blocked Days': 3
        })

        TaskManager.update_task_attributes(task, 5, "20/12/2024")
        self.assertEqual(task[TASK_END_DATE], datetime.date(2024, 12, 26))  # Expecting the task end date after blocking

if __name__ == '__main__':
    unittest.main()