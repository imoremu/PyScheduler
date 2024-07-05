from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock

from freezegun import freeze_time

import pandas as pd

from scheduler.project_task_scheduler import TaskManager

from scheduler.project_scheduler_constants import (
    TASK_AUX_ALLOCATABLE_RESOURCES, TASK_ID, TASK_PRIORITY, TASK_RESOURCES_MAX,
    TASK_RESTRICTION, TASK_REMAINING, TASK_GOAL
)

class TestTaskManager(unittest.TestCase):

    def setUp(self):
                
        # Setup a basic DataFrame for tasks
        self.tasks_df = pd.DataFrame({
            TASK_ID: [1, 2, 3],
            TASK_GOAL: ['Task1', 'Task2', 'Task3'],
            "Team": ["T1", "T2", "T1"],            
            TASK_PRIORITY: [2, 1, 2],
            TASK_REMAINING: [10, 0, 8],
            TASK_RESOURCES_MAX: [5, 5, 5],
            TASK_RESTRICTION: [None, None, None],
        })
    
        self.mock_resource_manager = MagicMock()
        self.mock_resource_manager.responsible_attr_names = ['Team']

        self.task_manager_week_period = TaskManager(self.tasks_df, self.mock_resource_manager)
        self.task_manager_day_period = TaskManager(self.tasks_df, self.mock_resource_manager, period_days_available=1)

    @freeze_time("2024-05-10")        
    @patch.object(TaskManager, 'allocate_resources')
    @patch.object(TaskManager, '_distribute_resources_same_priority_and_responsible_tasks')
    @patch.object(TaskManager, 'filter_tasks_by_restriction')
    def test_clean_used_resources_called(self, mock_filter_tasks, mock_distribute_resources, mock_allocate_resources):
        ''' Check that once update_task_schedule is called, clean_used_resources from ProjectUsedResourceManager is called with today date'''
        dates = ['12-05-2024', '19-05-2024']
        self.task_manager_week_period.update_task_schedule(dates)

        self.mock_resource_manager.clean_resources.assert_called_once()

        # As date is fake, it's better to check the date passed to the method by checking the calls directly        
        actual_date = self.mock_resource_manager.clean_resources.call_args[0][0]

        # Verify that the date passed is 2024-05-10
        expected_date = datetime(2024, 5, 10)

        self.assertEqual(actual_date.year, expected_date.year)
        self.assertEqual(actual_date.month, expected_date.month)
        self.assertEqual(actual_date.day, expected_date.day)  

    @freeze_time("2024-05-10")
    @patch.object(TaskManager, 'allocate_resources')
    @patch.object(TaskManager, '_distribute_resources_same_priority_and_responsible_tasks')
    @patch.object(TaskManager, 'filter_tasks_by_restriction')
    def test_filter_tasks_by_restriction_called(self, mock_filter_tasks, mock_distribute_resources, mock_allocate_resources):
        dates = ['12-05-2024', '19-05-2024']
                
        mock_filter_tasks.return_value = self.tasks_df        
        self.task_manager_week_period.update_task_schedule(dates)

        # Remember: TASK ID is changed to string in the TaskManager initialization
        completed_tasks = self.tasks_df.loc[self.tasks_df[TASK_ID] == "2", TASK_ID].tolist()

        self.assertEqual(mock_filter_tasks.call_count, 4)        
        mock_filter_tasks.assert_any_call(unittest.mock.ANY, completed_tasks, '12-05-2024')
        mock_filter_tasks.assert_any_call(unittest.mock.ANY, completed_tasks, '19-05-2024')

    @freeze_time("2024-05-10")
    @patch.object(TaskManager, '_distribute_resources_same_priority_and_responsible_tasks')
    @patch.object(TaskManager, 'filter_tasks_by_restriction')
    def test_distribute_resources_called_week_period(self, mock_filter_tasks, mock_distribute_resources):
        dates = ['12-05-2024', '19-05-2024']
        self.mock_resource_manager.obtain_goal_resources.return_value = 3
        mock_filter_tasks.return_value = self.tasks_df
        
        mock_distributed_df = self.tasks_df.copy()
        mock_distributed_df[TASK_AUX_ALLOCATABLE_RESOURCES] = [1, 2, 3]  # Example values
        mock_distribute_resources.return_value = mock_distributed_df
                         
        self.task_manager_week_period.update_task_schedule(dates)

        self.assertEqual(mock_distribute_resources.call_count, 4) # 2 dates and 2 priority groups

        first_call_args = mock_distribute_resources.call_args_list[0][0]
        
        task1ID = first_call_args[0].iloc[0][TASK_ID]
        self.assertEqual(task1ID, "2")

        task1Effort = first_call_args[1]
        self.assertEqual(task1Effort, 15)  # 3 resources * 5 effort

    @freeze_time("2024-05-10")
    @patch.object(TaskManager, '_distribute_resources_same_priority_and_responsible_tasks')
    @patch.object(TaskManager, 'filter_tasks_by_restriction')
    def test_distribute_resources_called_day_period(self, mock_filter_tasks, mock_distribute_resources):        

        dates = ['12-05-2024', '19-05-2024']
        self.mock_resource_manager.obtain_goal_resources.return_value = 3
        mock_filter_tasks.return_value = self.tasks_df
        
        mock_distributed_df = self.tasks_df.copy()
        mock_distributed_df[TASK_AUX_ALLOCATABLE_RESOURCES] = [1, 2, 3]  # Example values
        mock_distribute_resources.return_value = mock_distributed_df

        self.task_manager_day_period.update_task_schedule(dates)                        

        self.assertEqual(mock_distribute_resources.call_count, 4) # 2 dates and 2 priority groups

        first_call_args = mock_distribute_resources.call_args_list[0][0]
        
        task1ID = first_call_args[0].iloc[0][TASK_ID]
        self.assertEqual(task1ID, "2")

        task1Effort = first_call_args[1]
        self.assertEqual(task1Effort, 3) # 3 resources * 1 effort

    @freeze_time("2024-05-10")
    @patch.object(TaskManager, 'allocate_resources')
    @patch.object(TaskManager, '_distribute_resources_same_priority_and_responsible_tasks')
    @patch.object(TaskManager, 'filter_tasks_by_restriction')
    def test_allocate_resources_called(self, mock_filter_tasks, mock_distribute_resources, mock_allocate_resources):
        dates = ['12-05-2024', '19-05-2024']
        mock_filter_tasks.return_value = self.tasks_df
        
        mock_distributed_df = pd.DataFrame({
            TASK_ID: [1, 2, 3],
            TASK_PRIORITY: [1, 2, 1],            
            TASK_AUX_ALLOCATABLE_RESOURCES: [4, 2,5]
        })

        # Split mock_distributed_df based on the priority grouping and responsibilities
        # Assuming tasks with IDs 1 and 3 have the same priority and responsibility, while task with ID 2 has a different priority
        mock_distribute_resources.side_effect = [
            mock_distributed_df[mock_distributed_df[TASK_ID] == 1],  # First call with tasks 1 on the first date
            mock_distributed_df[mock_distributed_df[TASK_ID] == 2],  # Second call with task 2 on the first date
            mock_distributed_df[mock_distributed_df[TASK_ID] == 3],  # Third call with tasks 3 on the second date
            mock_distributed_df[mock_distributed_df[TASK_ID] == 2]   # Fourth call with task 2 on the second date
        ]

        self.task_manager_week_period.update_task_schedule(dates)

        self.assertEqual(mock_allocate_resources.call_count, 4)  # 1 call for each date and priority group

        first_call_args = mock_allocate_resources.call_args_list[0][0]
        
        task1ID = first_call_args[0][TASK_ID]
        self.assertEqual(task1ID, 1)

        task1Effort = first_call_args[1]
        self.assertEqual(task1Effort, 4) # 4 allocatable resources for task 1


    @freeze_time("2024-05-10")
    @patch.object(TaskManager, 'filter_tasks_by_restriction')
    @patch.object(TaskManager, '_distribute_resources_same_priority_and_responsible_tasks')
    @patch.object(TaskManager, 'allocate_resources')
    def test_update_task_schedule_output(self, mock_allocate_resources, mock_distribute_resources, mock_filter_tasks):
        dates = ['12-05-2024', '19-05-2024']      
        mock_distribute_resources.return_value[TASK_AUX_ALLOCATABLE_RESOURCES] = None
        mock_allocate_resources.return_value = self.tasks_df

        result_df = self.task_manager_week_period.update_task_schedule(dates)

        pd.testing.assert_frame_equal(result_df, self.tasks_df)

if __name__ == '__main__':
    unittest.main()