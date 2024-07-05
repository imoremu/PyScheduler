import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from scheduler.project_scheduler_constants import (
    TASK_AUX_ALLOCATABLE_RESOURCES, TASK_ID, TASK_PRIORITY, TASK_ESTIMATION, TASK_RESOURCES_MAX,
    TASK_RESTRICTION, TASK_REMAINING, TASK_START_DATE, TASK_END_DATE
)

from scheduler.project_task_scheduler import TaskManager

class TestTaskScheduleDistribution(unittest.TestCase):
    """Test cases focused on the scheduling update of tasks."""

    def setUp(self):
        # Create a tasks DataFrame to cover various cases
        self.tasks_df = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2', 'Task3', 'Task4', 'Task5', 'Task6', 'Task7', 'Task8'],
            TASK_PRIORITY: [1, 2, 3, 2, 5, 5, 6, 6],
            TASK_ESTIMATION: [25, 60, 20, 20, 10, 30, 60, 20],
            TASK_RESOURCES_MAX: [3, 3, 5, 4, 5, 6, 3, 4],
            TASK_RESTRICTION: [None, 'Task1', None, '2024/05/02', None, None, None, None],
            TASK_REMAINING: [25, 60, 20, 20, 10, 30, 60, 20],
            TASK_START_DATE: [None, None, None, None, None, None, None, None],
            TASK_END_DATE: [None, None, None, None, None, None, None, None],
            'Team': ['Team A', 'Team A','Team A', 'Team A', 'Team A', 'Team A', 'Team A', 'Team A'],
            'Project': ['Project X', 'Project Y', "*", "Project Y", "Project Z", "Project Z", "Project A", "Project A"],
            'Goal': ['A', 'B', "C", "D", "E","F","G","H"]
        })
        
        self.dates = ['2024/05/01', '2024/05/02', '2024/05/03', '2024/05/04']

        self.resource_manager = MagicMock()
        self.resource_manager.used_resources_df.columns.re 

        self.task_manager = TaskManager(self.tasks_df, self.resource_manager)                

    def test_task_distribution_with_just_one_task_by_resources_available(self):
        """Test task update with resources available"""        

        tasks = pd.DataFrame({
            TASK_ID: ['Task1'],
            TASK_REMAINING: [25],
            TASK_RESOURCES_MAX: [3]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 10)

        task = distributed_tasks.iloc[0]

        self.assertEqual(task[TASK_AUX_ALLOCATABLE_RESOURCES], 10)   

    def test_task_distribution_with_just_one_task_by_remaining(self):
        """Test task update with remaining."""        

        tasks = pd.DataFrame({
            TASK_ID: ['Task1'],
            TASK_REMAINING: [15],
            TASK_RESOURCES_MAX: [5]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 20)

        task = distributed_tasks.iloc[0]

        self.assertEqual(task[TASK_AUX_ALLOCATABLE_RESOURCES], 15)   

    def test_task_distribution_with_just_one_task_by_resources_max(self):
        """Test task update with resources max."""        

        tasks = pd.DataFrame({
            TASK_ID: ['Task1'],
            TASK_REMAINING: [25],
            TASK_RESOURCES_MAX: [3]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 20)

        task = distributed_tasks.iloc[0]

        self.assertEqual(task[TASK_AUX_ALLOCATABLE_RESOURCES], 15) # 3 res max * period days (5) 

    def test_task_distribution_with_same_priority_task_available_resources(self):

        tasks = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2'],
            TASK_REMAINING: [2, 6],
            TASK_RESOURCES_MAX: [5, 6]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 2, 1) # period 1

        task1 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task1'].iloc[0]
        task2 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task2'].iloc[0]

        self.assertEqual(task1[TASK_AUX_ALLOCATABLE_RESOURCES], 0.5)
        self.assertEqual(task2[TASK_AUX_ALLOCATABLE_RESOURCES], 1.5)   

    def test_task_distribution_with_same_priority_task_one_limited(self):

        tasks = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2'],
            TASK_REMAINING: [10, 30],
            TASK_RESOURCES_MAX: [1, 6]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 30)

        task1 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task1'].iloc[0]
        task2 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task2'].iloc[0]

        self.assertEqual(task1[TASK_AUX_ALLOCATABLE_RESOURCES], 5)
        self.assertEqual(task2[TASK_AUX_ALLOCATABLE_RESOURCES], 25) 


    def test_task_distribution_with_same_priority_task_both_limited(self):
        """Test task update with remaining."""        

        tasks = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2'],
            TASK_REMAINING: [5, 30],
            TASK_RESOURCES_MAX: [8, 8]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 40)

        task1 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task1'].iloc[0]
        task2 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task2'].iloc[0]

        self.assertEqual(task1[TASK_AUX_ALLOCATABLE_RESOURCES], 5)
        self.assertEqual(task2[TASK_AUX_ALLOCATABLE_RESOURCES], 30) 

    def test_task_distribution_with_several_same_priority_task_res_available(self):
        """Test task update with remaining."""        

        tasks = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2', 'Task3'],
            TASK_REMAINING: [20, 20, 40],
            TASK_RESOURCES_MAX: [3, 5, 8]
        })
        
        distributed_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(tasks, 20)

        task1 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task1'].iloc[0]
        task2 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task2'].iloc[0]
        task3 = distributed_tasks.loc[distributed_tasks[TASK_ID] == 'Task3'].iloc[0]

        self.assertEqual(task1[TASK_AUX_ALLOCATABLE_RESOURCES], 5)
        self.assertEqual(task2[TASK_AUX_ALLOCATABLE_RESOURCES], 5)
        self.assertEqual(task3[TASK_AUX_ALLOCATABLE_RESOURCES], 10) 

if __name__ == '__main__':
    unittest.main()