import unittest
from unittest.mock import Mock
import pandas as pd

from scheduler.project_task_scheduler import TaskManager
from scheduler.project_scheduler_constants import ( 
    TASK_ID, TASK_PRIORITY, TASK_RESOURCES_MAX, TASK_RESTRICTION, 
    TASK_REMAINING, TASK_START_DATE, TASK_END_DATE, TASK_GOAL
)

class TestTaskManager(unittest.TestCase):
    """ Unit tests for the TaskManager class."""
    def setUp(self):
        """ Create a TaskManager instance and a DataFrame with task data."""
        self.task_data = {
            TASK_ID: ["1", "2", "3"],
            TASK_REMAINING: [5.5, 0, "N/A"],
            TASK_PRIORITY: [1, 2, 1],
            TASK_RESOURCES_MAX: [2.5, 2, ""],
            TASK_RESTRICTION: [None, '2024-01-01', "1"],
            TASK_START_DATE: [None, '2023-12-01', None],
            TASK_END_DATE: [None, None, None],
            TASK_GOAL: ['Goal A', 'Goal B', 'Goal C'],            
        }
        self.tasks_df = pd.DataFrame(self.task_data)
        
        self.resource_manager = Mock()
        self.resource_manager.responsible_attr_names = ['Team', 'Project']
        self.tasks_df['Team'] = ['Team A', 'Team B', 'Team A']
        self.tasks_df['Project'] = ['Project X', 'Project Y', 'Project Z']                  



    def test_check_task_schedule_valid_values(self):
        """Check that the method does not raise an error when valid values are found."""
        TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_schedule_missing_columns(self):
        """Check that the method raises an error when columns are missing."""
        
        required_columns = [TASK_REMAINING]

        self.tasks_df.drop(columns=[TASK_REMAINING], inplace=True)

        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df, required_columns)    

    def test_check_task_schedule_negative_values(self):
        """Check that the method raises an error when negative values are found."""
        self.tasks_df.at[0, TASK_REMAINING] = -1  
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_schedule_missing_values(self):
        """Check that the method does not raise an error when missing values are found. Only a warning is displayed"""
        self.tasks_df.at[0, TASK_REMAINING] = pd.NA          
        TaskManager.check_task_schedule(self.tasks_df)
        

    def test_check_task_schedule_duplicated_ids(self):
        """Check that the method raises an error when duplicated IDs are found."""
        self.tasks_df.at[1, TASK_ID] = "1"  
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_schedule_invalid_remaining(self):
        """Check that the method raises an error when the remaining time is invalid."""
        self.tasks_df.at[0, TASK_REMAINING] = "Invalid remaining time"

        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_resources_max_invalid_values(self):
        """Prueba la detección de valores inválidos en TASK_RESOURCES_MAX."""
        # Configuración intencional de un valor inválido
        self.tasks_df.at[0, TASK_RESOURCES_MAX] = "invalid"
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_priority_invalid_values(self):
        """Prueba la detección de valores inválidos en TASK_PRIORITY."""
        # Configuración intencional de un valor inválido
        self.tasks_df.at[0, TASK_PRIORITY] = "high"
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_remaining_negative_values(self):
        """Prueba la detección de valores negativos en TASK_REMAINING."""
        # Configuración intencional de un valor negativo
        self.tasks_df.at[0, TASK_REMAINING] = -1
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_resources_max_negative_values(self):
        """Prueba la detección de valores negativos en TASK_RESOURCES_MAX."""
        # Configuración intencional de un valor negativo
        self.tasks_df.at[0, TASK_RESOURCES_MAX] = -5
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)

    def test_check_task_priority_negative_values(self):
        """Prueba la detección de valores negativos en TASK_PRIORITY."""
        # Configuración intencional de un valor negativo
        self.tasks_df.at[0, TASK_PRIORITY] = -2
        with self.assertRaises(ValueError):
            TaskManager.check_task_schedule(self.tasks_df)    