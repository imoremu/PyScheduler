import unittest
import pandas as pd
import json

from scheduler.project_task_scheduler import TaskManager

class TestGenerateResponsibilityKey(unittest.TestCase):
    def setUp(self):
        """Create a mock DataFrame to use for testing."""
        data = {
            'Resource1': ['Alice', 'Bob', None],
            'Resource2': [1, 2, 3],
            'Resource3': ['X', 'Y', 'Z']
        }
        
        self.df = pd.DataFrame(data)

    def test_multiple_columns(self):
        """Test with multiple responsibility columns."""
        row = self.df.iloc[0]
        columns = ['Resource1', 'Resource2', 'Resource3']
        expected_key = json.dumps({'Resource1': 'Alice', 'Resource2': 1, 'Resource3': 'X'})
        generated_key = TaskManager.generate_responsibility_key(row, columns)
        self.assertEqual(generated_key, expected_key)

    def test_with_none_values(self):
        """Test case where one of the columns has None values."""
        row = self.df.iloc[2]
        columns = ['Resource1', 'Resource2', 'Resource3']
        expected_key = json.dumps({'Resource1': None, 'Resource2': 3, 'Resource3': 'Z'})
        generated_key = TaskManager.generate_responsibility_key(row, columns)
        self.assertEqual(generated_key, expected_key)

    def test_numeric_values(self):
        """Test case with numeric columns."""
        row = self.df.iloc[1]
        columns = ['Resource2']
        expected_key = json.dumps({'Resource2': 2})
        generated_key = TaskManager.generate_responsibility_key(row, columns)
        self.assertEqual(generated_key, expected_key)

    def test_empty_columns(self):
        """Test with an empty list of columns."""
        row = self.df.iloc[0]
        columns = []
        expected_key = json.dumps({})
        generated_key = TaskManager.generate_responsibility_key(row, columns)
        self.assertEqual(generated_key, expected_key)

if __name__ == '__main__':
    unittest.main()
