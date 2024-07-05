import unittest
import pandas as pd
from unittest.mock import patch

from scheduler.project_used_resources_initializer import ProjectUsedResourceManagerInitializer

from scheduler.project_scheduler_constants import ACCUMULATED_SYNONYMS, USED_RESOURCE_GOAL, USED_RESOURCE_NA

from utils.logger import create_logger
logger = create_logger(__name__)

class TestProjectUsedResourceInitializer(unittest.TestCase):
    def setUp(self):        
        self.tasks_df = pd.DataFrame({
            'ID': ['1', '2', '3', '4', '5'],
            'Goal': ['Goal1', 'Goal2', 'Goal3', 'Goal4', 'Goal5'],
            'Task': ['Task1', 'Task2', 'Task3', 'Task4', 'Task5'],
            'Team': ['Team A', 'Team A', 'Team B', 'Team B', 'Team A'],
            'Remaining': [2, 1, 2, 0,"N/A"],
            'Project': ['Project X', 'TOTAL', 'Project Y', 'Project Y', 'Project X'],
            'Priority': ['=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))', 
                         '=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))', 
                         '=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))',
                         '=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))',
                         'N/A'],
            'Type': ['Documental', 'HW' , 'SW', 'SW', 'Documental']
        })
        
        # Existing used resources data, including the 'Priority' column with Excel formulas
        self.used_resources_df = pd.DataFrame({
            USED_RESOURCE_GOAL: ['Goal1', 'Goal2', '*','*'],
            'Team': ['Team A', 'Team A','Team B','Team B'],
            'Project': ['Project X', 'Project Y', '*', 'Project Y'],            
            'Priority': [
                '=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))',
                '=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))',                                
                'N/A',                                
                'N/A'                                
            ],
            'Type':[
                '=INDICE(T_Schedule[Tipo], COINCIDIR([Goal], T_Schedule[goal], 0))',
                '=INDICE(T_Schedule[Tipo], COINCIDIR([Goal], T_Schedule[goal], 0))',
                'N/A',                                
                'N/A'                                
            ],
            '11/10/2024': [5, 3, 2, 1],
            '18/10/2024': [3, 2, 4, 3], 
        })
        
        self.responsible_df = pd.DataFrame({
            'Team': ['Team A', 'Team A', 'Team B'],
            'Project': ['*', 'Project Y', '*']
        })

        self.initializer = ProjectUsedResourceManagerInitializer(self.used_resources_df, self.tasks_df, self.responsible_df)

    def test_initial_state(self):
        """Ensure that the DataFrame and attributes are initialized correctly."""
        self.assertIsNotNone(self.initializer.used_resources_df)
        self.assertIsNotNone(self.initializer.tasks_df)
        self.assertEqual(self.initializer.responsible_attr_names, ['Team', 'Project'])                    

        expected_date_columns = ['11/10/2024', '18/10/2024']

        self.assertEqual(self.initializer.date_columns, expected_date_columns)        
        
        expected_info_columns = ['Priority','Type']
        self.assertEqual(self.initializer.info_columns, expected_info_columns)

    @patch.object(ProjectUsedResourceManagerInitializer, '_add_new_task_rows')
    @patch.object(ProjectUsedResourceManagerInitializer, '_initialize_resource_columns')
    def test_initialize_used_resources_calls_internal_methods(self, mock_initialize_resource_columns, mock_add_new_task_rows):       
        """Test to verify that the all init actions:
        - add new task rows
        - initialize resource columns
        are done."""        
        self.initializer.initialize_used_resource_manager()

        # Verificar que se llamaron los métodos internos
        mock_add_new_task_rows.assert_called_once()
        mock_initialize_resource_columns.assert_called_once()

    def test_integration_of_tasks_into_resources(self):
        """Ensure that all tasks from the task DataFrame are represented in the used resources DataFrame."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        # Expected Tasks: those with remaining numeric and > 0
        expected_tasks = set(['Goal1', 'Goal2', 'Goal3', '*'])

        current_tasks = set(updated_resources[USED_RESOURCE_GOAL].unique())
        
        self.assertEqual(expected_tasks, current_tasks)

    def test_preservation_of_existing_resources(self):
        """Check that existing resources are maintained during initialization."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        existing_value = updated_resources.loc[updated_resources[USED_RESOURCE_GOAL] == 'Goal1', '11/10/2024'].iloc[0]
        self.assertEqual(existing_value, 5)

    def test_addition_of_new_tasks(self):
        """Test the addition of new tasks to the used resources DataFrame."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        self.assertIn("Goal2", updated_resources[USED_RESOURCE_GOAL].values)  # Check that Goal 2 is present

    def test_default_initialization_of_resources(self):
        """Test that the resources for new tasks are initialized to 0."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        self.assertTrue((updated_resources.loc[updated_resources[USED_RESOURCE_GOAL] == 'Goal3', '11/10/2024'] == 0).all())

    def test_wildcard_resources_new_wildcard_row(self):
        """Test that the resources for wildcard tasks (Team A, *) are initialized to the sum of related tasks."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df

        # Verify Team A and Project * have a total sum of 8 for 11/10/2024
        expected_resources_team_a_all = 8
        actual_resources_team_a_all = updated_resources.loc[
            (updated_resources[USED_RESOURCE_GOAL].isin(ACCUMULATED_SYNONYMS)) &
            (updated_resources['Team'] == 'Team A') &
            (updated_resources['Project'] == '*'),
            '11/10/2024'
        ].iloc[0]

        self.assertEqual(actual_resources_team_a_all, expected_resources_team_a_all,
                        f'Expected resources for Team A, * on 11/10/2024: {expected_resources_team_a_all}, but got: {actual_resources_team_a_all}')


    def test_wildcard_resources_specific_responsability_row(self):
        """Test that the resources for wildcard tasks (Team A, Project Y) are initialized to the sum of related tasks."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df

        # Verify Team A and Project Y have a total sum of 3 for 18/10/2024
        expected_resources = 2
        actual_resources = updated_resources.loc[
            (updated_resources[USED_RESOURCE_GOAL].isin(ACCUMULATED_SYNONYMS)) &
            (updated_resources['Team'] == 'Team A') &
            (updated_resources['Project'] == 'Project Y'),
            '18/10/2024'
        ].iloc[0]

        self.assertEqual(actual_resources, expected_resources,
                        f"Expected resources for Team A, Project Y on 18/10/2024: {expected_resources}, but got: {actual_resources}")


    def test_wildcard_resources_already_defined_wildcard_row(self):    
        """Test that wildcard tasks sum up resources correctly in general."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df

        expected_resources_general = 4 
        actual_resources_general = updated_resources.loc[
            (updated_resources[USED_RESOURCE_GOAL].isin(ACCUMULATED_SYNONYMS)) &
            (updated_resources['Team'] == 'Team B') &
            (updated_resources['Project'] == '*'),
            '18/10/2024'
        ].iloc[0]

        self.assertEqual(actual_resources_general, expected_resources_general,
                     f"Expected resources for Team A, * on 11/10/2024: {expected_resources_general}, but got: {actual_resources_general}")
        
    def test_responsibility_groups_in_resources(self):
        """Ensure that each specific responsibility group is represented in the used resources DataFrame for '*' goal entries."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        
        # ('Team A', 'Project X') is not included as there is neither available resources nor task associated to goal '*' 
        # so there is no need to store it
        expected_groups = set([
            ('Team A', '*'),               
            ('Team A', 'Project Y'),
            ('Team B', '*'),
            ('Team B', 'Project Y')
        ])
        
        actual_groups = set(updated_resources[updated_resources[USED_RESOURCE_GOAL] == '*'][['Team', 'Project']].apply(tuple, axis=1))
        
        self.assertEqual(expected_groups, actual_groups)

    def test_specific_task_priority_formula_inclusion(self):
        """Ensure that task priorities for specific tasks are included in the used_resources_df using correct Excel formulas."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        expected_formula = '=INDICE(T_Schedule[Priority], COINCIDIR([Goal], T_Schedule[goal], 0))'
        actual_formula = updated_resources.loc[updated_resources[USED_RESOURCE_GOAL] == "Goal2", 'Priority'].iloc[0]
        self.assertEqual(actual_formula, expected_formula)

    def test_wildcard_task_priority_inclusion(self):
        """Ensure that tasks with a wildcard USED_RESOURCE_GOAL_NAME have 'N/A' for their priority."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        actual_na = updated_resources.loc[updated_resources[USED_RESOURCE_GOAL].isin(ACCUMULATED_SYNONYMS), 'Priority'].iloc[0]
        self.assertEqual(actual_na, USED_RESOURCE_NA)

    def test_no_duplicate_rows_based_on_responsible_df(self):
        """Ensure there are no duplicate rows in the used_resources_df considering columns from responsible_df."""
        updated_resources = self.initializer.initialize_used_resource_manager().used_resources_df
        columns_to_check = self.responsible_df.columns.tolist()
        columns_to_check.append(USED_RESOURCE_GOAL)
        
        logger.debug(f"The responsible values on used resources are: {str(updated_resources[columns_to_check])}")

        duplicated_rows = updated_resources.duplicated(subset=columns_to_check).sum()
        self.assertEqual(duplicated_rows, 0, f'Found {duplicated_rows} duplicate rows based on responsible columns')

# Run the tests
if __name__ == '__main__':
    unittest.main()