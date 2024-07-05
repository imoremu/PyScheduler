'''
Created on 2 ene. 2019

@author: imoreno
'''
import unittest
import os
from utils import resourcesmanager


class Test(unittest.TestCase):


    def test_get_relative_config_file(self):
        
        conf_file = os.path.join(".", "tests", "unit", "utils", "conf", "test.file")
        
        expected = os.path.normcase(os.path.join(os.path.dirname(__file__), "conf", "test.file"))
        
        result = os.path.normcase(resourcesmanager.get_resource_path(conf_file))
        
        self.assertEqual(result, expected, "Resource File should be {0} and is {1}".format(expected, result)) 
        pass

    def test_create_dir(self):
        DEFAULT_CONF_FILE = resourcesmanager.get_resource_path(os.path.join("output", "test_create_dir", "test.yaml"))
        
        path = os.path.dirname(DEFAULT_CONF_FILE)
        
        if os.path.exists(path):
            os.rmdir(path)
        
        resourcesmanager.create_path_if_needed(DEFAULT_CONF_FILE)                
        
        self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()