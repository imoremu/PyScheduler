import unittest

import pandas as pd

from scheduler.project_scheduler_constants import TASK_END_DATE, TASK_ID, TASK_REMAINING
from scheduler.project_task_scheduler import TaskManager

class TestTaskCleanEndDates(unittest.TestCase):    
    
    def setUp(self):

        self.tasks_df = pd.DataFrame({
            TASK_ID: ['Task1', 'Task2', 'Task3', 'Task4'],
            TASK_END_DATE: ['22/05/2024', '24/05/2024', '25/05/2024', '26/05/2024'],
            TASK_REMAINING: [0, 5, 0, 3]
        })

    def test_tasks_with_no_remaining_work(self):
        # All tasks with no remaining work should keep their end dates.
        TaskManager.clean_end_dates(self.tasks_df)
        self.assertEqual(self.tasks_df.loc[self.tasks_df[TASK_REMAINING] == 0, TASK_END_DATE].tolist(), ['22/05/2024', '25/05/2024'])

    def test_tasks_with_remaining_work(self):
        # All tasks with remaining work should have their end dates removed.
        TaskManager.clean_end_dates(self.tasks_df)
        self.assertTrue(self.tasks_df.loc[self.tasks_df[TASK_REMAINING] > 0, TASK_END_DATE].isnull().all())

    def test_empty_task_list(self):
        # Handling an empty DataFrame.
        empty_df = pd.DataFrame(columns=[TASK_ID, TASK_END_DATE, TASK_REMAINING])
        TaskManager.clean_end_dates(empty_df)
        self.assertTrue(empty_df.empty)

if __name__ == '__main__':
    unittest.main()
