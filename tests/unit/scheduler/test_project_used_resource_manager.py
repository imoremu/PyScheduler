import unittest

import pandas as pd

from utils.app_config import AppConfig
from utils.util_constants import CONF_DAYFIRST

AppConfig()[CONF_DAYFIRST] = True

from scheduler.project_scheduler_constants import ALL_TAG
from scheduler.project_used_resource_manager import ProjectUsedResourceManager

from freezegun import freeze_time

class TestProjectUsedResourceManager(unittest.TestCase):

    def setUp(self):                
       
        # None added in a date column means that there is no resource assigned for that task on that date
        # It's added to assure that the method works correctly with None values
        self.used_resources_data = pd.DataFrame({
            'Task':         ['A',         'B',         'C',        'D',      '*',         'Test/RE/[2]'],
            'Team':         ['Team A',    'Team/[B]',  'Team/[B]', 'Team C', '*',         'Team A'],
            'Project':      ['Project X', 'Project Y', 'TOTAL',    '*',      'Project X', 'Project X'],
            'Priority':     [1,            50,         100,        200,      20,          30],
            '11/10/2024':   [1,            2,          5,          1,        2,           3],
            '18/10/2024':   [2,            2,          None,       3,        3,           None],
            '25/10/2024':   [2,            2,          4,          5,        4,           1],
            '1/11/2024':    [2,            2,          2,          3,        5,           0]
        })
        
        # Instanciar ProjectResourceManager
        self.manager = ProjectUsedResourceManager(self.used_resources_data)
   
    def test_clean_future_resources(self):        
        expected_data = self.used_resources_data 

        for date in ['18/10/2024', '25/10/2024', '1/11/2024']:
            expected_data[date] = [0.0] * len(expected_data[date])
        
        self.manager.clean_used_resources('18/10/2024')
        
        pd.testing.assert_frame_equal(self.manager.used_resources_df, expected_data)

    def test_clean_all_resources_if_date_is_early(self):
        expected_data = self.used_resources_data  

        for date in ['11/10/2024', '18/10/2024', '25/10/2024', '1/11/2024']:
            expected_data[date] = [0.0] * len(expected_data[date])

        self.manager.clean_used_resources('11/10/2024')

        pd.testing.assert_frame_equal(self.manager.used_resources_df, expected_data)

    def test_no_cleaning_if_no_future_dates(self):
        self.manager.clean_used_resources('2/11/2024')
        expected_data = pd.DataFrame(self.used_resources_data.fillna(0)) 
        pd.testing.assert_frame_equal(self.manager.used_resources_df, expected_data)

    def test_obtain_used_goal_resources_specific_date_and_filters(self):
        # Prueba con filtros específicos en una fecha dada
        result = self.manager.obtain_used_goal_resources('11/10/2024', Team='Team/[B]', Project='Project Y')
        self.assertEqual(result, 2, "Debería calcular correctamente los recursos usados para Team/[B] en Project Y el 11/10/2024")

    def test_obtain_used_goal_resources_all_tag(self):
        # Prueba usando el ALL_TAG para incluir todos los equipos
        result = self.manager.obtain_used_goal_resources('18/10/2024', Project=ALL_TAG)
        self.assertEqual(result, 3, "Debería calcular correctamente los recursos usados por el equipo * el 18/10/2024")

    def test_obtain_used_goal_resources_with_wrong_responsible(self):
        # Prueba usando el TOTAL_TAG para un proyecto
        result = self.manager.obtain_used_goal_resources('25/10/2024', Team='Team/[B]', Project=ALL_TAG)
        self.assertEqual(result, 4, "Debería sumar todos los recursos usados en para el Team/[B] y Project * para la fecha 25/10/2024")

    def test_obtain_used_goal_resources_date_not_exist(self):
        # Prueba intentando acceder a una fecha que no existe
        with self.assertRaises(ValueError):
            self.manager.obtain_used_goal_resources('12/12/2024', Team='Team A')

    def test_obtain_used_goal_resources_no_filters(self):
        # Prueba sin filtros, sumando todos los recursos para una fecha
        result = self.manager.obtain_used_goal_resources('1/11/2024')
        self.assertEqual(result, 14, "Debería sumar todos los recursos usados en la fecha 1/11/2024")

    def test_obtain_used_goal_resources_dict(self):
        # Prueba sin filtros, sumando todos los recursos para una fecha
        filter_conditions = {"Team":"Team C", "Project":"*"}
        result = self.manager.obtain_used_goal_resources('1/11/2024', **filter_conditions)
        self.assertEqual(result, 3, "Debería sumar todos los recursos usados en para el Team C y Project * en la fecha 1/11/2024")

    def test_update_specific_resource_increase(self):
        """ Prueba aumentar recursos específicos sin comodines """
        self.manager.update_used_resources('18/10/2024', 2, Team='Team A', Project='Project X')
        
        expected_task_A = 4  # Original era 2, sumamos 2
        expected_task_B = 2  # Original era 2, no sumamos        
        expected_task_C = 0  # Original era None, no sumamos    
        expected_task_D = 3  # Original era 1, no sumamos        
        expected_task_all = 5  # Original era 3, sumamos 2, dado que Task * de la lista casa con cualquier valor de filter conditions 
        expected_task_E = 2  # Original era None, sumamos 2

        actual_task_A = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'A'), '18/10/2024'].iloc[0]
        actual_task_B = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'B'), '18/10/2024'].iloc[0]
        actual_task_C = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'C'), '18/10/2024'].iloc[0]
        actual_task_D = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'D'), '18/10/2024'].iloc[0]
        actual_task_all = self.manager.used_resources_df.loc[((self.manager.used_resources_df['Task'] == ALL_TAG) & (self.manager.used_resources_df['Project'] == 'Project X')), '18/10/2024'].iloc[0]
        actual_task_E = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'Test/RE/[2]'), '18/10/2024'].iloc[0]

        self.assertEqual(actual_task_A, expected_task_A)
        self.assertEqual(actual_task_B, expected_task_B)
        self.assertEqual(actual_task_C, expected_task_C)
        self.assertEqual(actual_task_D, expected_task_D)
        self.assertEqual(actual_task_all, expected_task_all)
        self.assertEqual(actual_task_E, expected_task_E)

    def test_update_using_wildcard_project(self):
        """ Prueba actualizar utilizando comodín en proyectos donde project = '*' """
        self.manager.update_used_resources('18/10/2024', 1, True, Team='Team/[B]', Project='*')
        
        expected_task_A = 2  # Original era 2, no sumamos
        expected_task_B = 2  # Original era 2, no sumamos
        expected_task_C = 1  # Original era None, sumamos 1
        expected_task_D = 3  # Original era 1, sumamos 1        
        expected_task_all = 3  # Original era 3, no sumamos dado que Project X de la lista no casa con Project * de los filter conditions
        
        actual_task_A = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'A'), '18/10/2024'].iloc[0]
        actual_task_B = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'B'), '18/10/2024'].iloc[0]
        actual_task_C = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'C'), '18/10/2024'].iloc[0]
        actual_task_D = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'D'), '18/10/2024'].iloc[0]
        actual_task_all = self.manager.used_resources_df.loc[((self.manager.used_resources_df['Task'] == ALL_TAG) & (self.manager.used_resources_df['Project'] == 'Project X')), '18/10/2024'].iloc[0]
        
        self.assertEqual(actual_task_A, expected_task_A)
        self.assertEqual(actual_task_B, expected_task_B)        
        self.assertEqual(actual_task_C, expected_task_C)
        self.assertEqual(actual_task_D, expected_task_D)
        self.assertEqual(actual_task_all, expected_task_all)

    def test_set_update_resources_increase_false(self):
        """ Prueba establecer un valor específico para los recursos utilizados """
        self.manager.update_used_resources('18/10/2024', 10, False, Task='B')
        expected = 10  # Establecemos a 10, sin importar el valor original
        actual = self.manager.used_resources_df.loc[(self.manager.used_resources_df['Task'] == 'B'), '18/10/2024'].iloc[0]
        self.assertEqual(actual, expected)

    def test_no_change_for_non_matching_filters(self):
        """ Asegurarse de que no se realizan cambios si los filtros no coinciden con ninguna fila """
        self.manager.update_used_resources('18/10/2024', 5, True, Team='Team Z', Project='Project Z')
        expected = self.used_resources_data['18/10/2024'].fillna(0).copy()  # Debería ser igual ya que no hay coincidencias
        pd.testing.assert_series_equal(self.manager.used_resources_df['18/10/2024'], expected)

if __name__ == '__main__':
    unittest.main()