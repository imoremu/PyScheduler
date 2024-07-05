import unittest
from unittest.mock import MagicMock
import pandas as pd

from utils.app_config import AppConfig

from utils.util_constants import CONF_DAYFIRST
AppConfig()[CONF_DAYFIRST] = True

from scheduler.project_used_resource_manager import ProjectUsedResourceManager
from scheduler.project_scheduler_constants import USED_RESOURCE_GOAL
from scheduler.project_resource_manager import ProjectResourceManager

class TestProjectResourceManager(unittest.TestCase):
    
    def setUp(self):

        # Sample data for available resources
        self.available_resources_df = pd.DataFrame({
            'Team': ['Team A', 'Team A', 'Team B', 'Team B'],
            'Project': ['*', 'Project X', '*', 'Project Y' ],
            'Goal': ['*', 'Task1', '*', '*'],
            '11/10/2024': [5, 3, 4, 3],
            '18/10/2024': [6, 4, 5, 3]
        })

        # Sample data for used resources
        self.used_resources_df = pd.DataFrame({
            'Team': ['Team A', 'Team A', 'Team B', 'Team B', 'Team B'],
            'Project': ['*', 'Project X', '*', 'Project Y', 'Project Y'],
            'Goal': ['*', 'Task1', '*','*','Task2'],
            '11/10/2024': [4, 1, 1, 3, 3],
            '18/10/2024': [3, 2, 6, 2, 2]
        })

        # Sample data for tasks (Schedule)
        self.tasks_df = pd.DataFrame({
            'ID': ['Task1', 'Task2', 'Task3'],
            'Team': ['Team A', 'Team B', 'Team A'],
            'Project': ['Project X', 'Project Y', '*'],
            'Goal': ['Task1', 'Task2', 'Task3'],
            'Priority': [1, 2, 3],
            'Resources Max.': [1,2,4],
            'Remaining': [2,1,2]
        })

        # Create instance of resource manager
        self.resource_manager = ProjectResourceManager(self.available_resources_df, self.used_resources_df, self.tasks_df)

    def test_initialization(self):
        """Test to verify the correct initialization of the resource manager."""
        self.assertIsNotNone(self.resource_manager.available_resources_df)        
        self.assertIsNotNone(self.resource_manager.responsible_df)
        self.assertIsInstance(self.resource_manager.used_resources_manager, ProjectUsedResourceManager)
        self.assertIsNotNone(self.resource_manager.used_resources_manager.used_resources_df)

    def test_missing_columns_in_used_resources(self):
        """Test to ensure errors are raised when responsibility columns are missing in the used resources DataFrame."""
        incomplete_used_resources_df = pd.DataFrame({
            'Team': ['Team A', 'Team A'],
            'Goal': ['*', 'Task1'],
            '11/10/2024': [4, 1],
            '18/10/2024': [5, 2]
        })

        with self.assertRaises(ValueError):
            ProjectResourceManager(self.available_resources_df, incomplete_used_resources_df, self.tasks_df)

    def test_missing_columns_initialization(self):
        """Test to verify errors are raised when responsibility columns are missing in the tasks DataFrame."""
        incomplete_tasks_df = pd.DataFrame({
            'ID': ['Task1', 'Task2', 'Task3'],
            'Project': ['Project X', 'Project Y', '*'],
            'Priority': [1, 2, 3]
        })

        with self.assertRaises(ValueError):
            ProjectResourceManager(self.available_resources_df, self.used_resources_df, incomplete_tasks_df)

    def test_mismatched_date_columns(self):
        """Test to ensure an error is raised when date columns do not match."""
        mismatched_used_resources_df = pd.DataFrame({
            'Team': ['Team A', 'Team A'],
            'Project': ['*', 'Project X'],
            'Goal': ['*', 'Task1'],
            '11/10/2024': [4, 1],
            '19/10/2024': [3, 1]
        })

        with self.assertRaises(ValueError):
            ProjectResourceManager(self.available_resources_df, mismatched_used_resources_df, self.tasks_df)

    def test_obtain_resources_for_specific_responsibility (self):
        """Test to verify resources for Team A, Project X, Task1 on 11/10/2024."""
        # Resources for Team A / Project X = 3 - 1 = 2
        # Resources for Team A / * = 5 - 4 = 1
        # Expected result: min --> 1
        # Added extra attr to check that extra non responsible attributes are accepted.
        filters = {'Team': 'Team A', 'Project': 'Project X', USED_RESOURCE_GOAL: 'Task1', 'Extra' : 'Extra Attr'}
        result = self.resource_manager.obtain_goal_resources('11/10/2024', **filters)
        self.assertEqual(result, 1)

    def test_obtain_resources_for_wildacard_responsibility (self):
        """Test to verify resources for Team B, * on 18/10/2024."""
        # Resources for Team B / * = 4 - 1 = 3
        # Expected result: 3
        filters = {'Team': 'Team B', 'Project': '*', USED_RESOURCE_GOAL: '*'}
        result = self.resource_manager.obtain_goal_resources('11/10/2024', **filters)
        self.assertEqual(result, 3)

    def test_negative_resources(self):
        """Test to verify that if available resources are less than used, the result is 0."""
        # Resources for Team B / * on 11/10/2024: 5 - 6 = -1
        # Resources for Team B / Project Y: 3 - 2 = 1
        # Expected result: 0
        filters = {'Team': 'Team B', 'Project': 'Project Y', USED_RESOURCE_GOAL: '*'}
        result = self.resource_manager.obtain_goal_resources('18/10/2024', **filters)
        self.assertEqual(result, 0)

    def test_negative_case_no_resources(self):
        """Test to verify that no resources are available when a date column is missing."""
        with self.assertRaises(ValueError):
            self.resource_manager.obtain_goal_resources('19/10/2024', Team='Team A', Project='Project X', Goal='Task1')

    def test_successful_update(self):
        
        # Mock used_resources_manager
        self.used_resources_manager = MagicMock()
        self.resource_manager.used_resources_manager = self.used_resources_manager

        self.resource_manager.update_goal_resources('01/01/2024', 5, Team='Team A', Project='Project X', Goal='Goal1')
        self.used_resources_manager.update_used_resources.assert_called_once_with(
            '01/01/2024', 5, True, Team='Team A', Project='Project X', Goal='Goal1'
        )
        
    
    def test_update_with_not_all_filter_attrs(self):
        
        # Mock used_resources_manager
        self.used_resources_manager = MagicMock()
        self.resource_manager.used_resources_manager = self.used_resources_manager

        self.resource_manager.update_goal_resources('01/01/2024', 5, Team="Team A")
        self.used_resources_manager.update_used_resources.assert_called_once_with(
            '01/01/2024', 5, True, Team="Team A"
        )
        
    def test_update_with_no_filter_attrs(self):
        
        # Mock used_resources_manager
        self.used_resources_manager = MagicMock()
        self.resource_manager.used_resources_manager = self.used_resources_manager

        self.resource_manager.update_goal_resources('01/01/2024', 5)
        self.used_resources_manager.update_used_resources.assert_called_once_with(
            '01/01/2024', 5, True
        )

    def test_update_with_extra_filter_attrs(self):
        
        # Mock used_resources_manager
        self.used_resources_manager = MagicMock()
        self.resource_manager.used_resources_manager = self.used_resources_manager

        self.resource_manager.update_goal_resources('01/01/2024', 5, Team="Team A", Extra="Extra")
        self.used_resources_manager.update_used_resources.assert_called_once_with(
            '01/01/2024', 5, True, Team="Team A"
        )    
        

if __name__ == '__main__':
    unittest.main()