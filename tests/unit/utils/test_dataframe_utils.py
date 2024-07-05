'''
Created on 30 mar. 2021

@author: imoreno
'''
import unittest

from utils import resourcesmanager
from utils.data.dataframe_utils import data_filter_by_dataframe, data_filter_by_dict

import os

from pandas.core.frame import DataFrame
from datetime import datetime

ORIGINAL_DATAFRAME = DataFrame.from_dict({"A": [1,2,3,4,5,6,7,8,9,0],
                                          "B": [11,12,13,14,15,16,17,18,19,10],
                                          "C": [21,22,23,24,25,26,27,28,29,20],
                                          "D": [31,32,33,34,35,36,37,38,39,30]})

FILTER_DATAFRAME = DataFrame.from_dict({  "B": [11,13,16,10],
                                          "D": [31,33,36,30],
                                          "A": [1,3,5,0]})
 

BASE_DATA_DICT = {
        'Name':['Alisa','Bobby','Cathrine','Alisa','Bobby','Cathrine',
                'Alice','Bobby','Cathrine','Alisa','Bobby','Cathrin'],
        'Exam':['Semester 1','Semester 1','Semester 1','Semester 1','Semester 1','Semester 1',
                'Semester 2','Semester 2','Semester 2','Semester 2','Semester 2','Semester 2'],
     
        'Subject':['Mathematics','Mathematics','Mathematics','Science','Science','Science',
                   'Mathematics','Mathematics','Mathematics','Science','Science','Science'],
        'Score':[65,42,52,78,51,87,95,73,42,65,86,89],
        'Previous Score':[62,47,55,74,31,77,85,63,42,67,89,81],
        'Exam Date': [datetime(2019,1,24),datetime(2019,1,24),datetime(2019,1,24),datetime(2019,1,26),datetime(2019,1,26),datetime(2019,1,26),
                      datetime(2019,5,14),datetime(2019,5,14),datetime(2019,5,14),datetime(2019,5,19),datetime(2019,5,19),datetime(2019,5,19)]
        }
 
BASE_DATAFRAME = DataFrame(BASE_DATA_DICT, columns=['Name','Exam','Subject','Score', 'Previous Score', 'Exam Date'])
    
class TestDataFrameUtils(unittest.TestCase):
    
    def setUp(self):
               
        self.data = BASE_DATAFRAME

    def tearDown(self):
        pass

    def testFilterByDataframe(self):
        result = data_filter_by_dataframe(FILTER_DATAFRAME, ORIGINAL_DATAFRAME).to_dict("list")
        
        expected = {"A": [1,3,0],
                    "B": [11,13,10],
                    "C": [21,23,20],
                    "D": [31,33,30]}
        
        self.assertEqual(result, expected)
       
    def testObtainFilteredRowsByOneAttribute(self):
      
        result = len(data_filter_by_dict({"Name" : "Bobby"}, self.data))
        
        self.assertEqual(result, 4, 
                    "Obtained number of rows for Bobby is: {0} \n Expected: {1}".format(result, 4))  
        
    
    def testObtainFilteredRowsByInequality(self):
      
        result = len(data_filter_by_dict({"Score" : "< 55"}, self.data))
        
        self.assertEqual(result, 4, 
                    "Obtained number of rows for score > 74  is: {0} \n Expected: {1}".format(result, 4))  
        
    def testObtainFilteredRowsByCallable(self):
      
        result = len(data_filter_by_dict({"Callable" : lambda df: df['Exam Date'] < datetime(2019,5,19)}, self.data))
        
        self.assertEqual(result, 9, 
                    "Obtained number of rows for date < 19/05/2019  is: {0} \n Expected: {1}".format(result, 9))  
    
    def testObtainFilteredRowsByInequalityWithSpaces(self):
      
        result = len(data_filter_by_dict({"Previous Score" : "> 73"}, self.data))
        
        self.assertEqual(result, 5, 
                    "Obtained number of rows for score > 74  is: {0} \n Expected: {1}".format(result, 5))  
        
    def testObtainFilteredRowsByMoreThanOneAttribute(self):
      
        result = len(data_filter_by_dict({"Exam" : "Semester 1", "Subject" : "Science"}, self.data))
        
        self.assertEqual(result, 3, 
                    "Obtained number of rows for Science exam in Semester 1 is: {0} \n Expected: {1}".format(result, 3))  

                       
    def testObtainListQuery(self):
        
        query = [{"Name" : "Bobby"},{"Subject" : "Mathematics"}]
        
        result = len(data_filter_by_dict(query, self.data))                
        
        self.assertEqual(result, 8, 
                    "Obtained number of rows for Bobby or Mathematics is: {0} \n Expected: {1}".format(result, 8))  


    def testObtainListQueryInKey(self):
        
        query = {"Name Filter" : [{"Name" : "Cathrin"}, {"Subject" : "Mathematics"}], "Exam" : 'Semester 2'}
        
        result = len(data_filter_by_dict(query, self.data))                
        
        self.assertEqual(result, 4, 
                    "Obtained number of rows for Cathrin or Mathematics is: {0} \n Expected: {1}".format(result, 4))  

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()