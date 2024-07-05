# Copyright (c) 2024 - Iván Moreno 
#  
# This software is licensed under the MIT License.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# pandas_conf imported to avoid the warning: "SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame."
import scheduler.pandas_conf

from utils.app_config import AppConfig

import pandas as pd

from utils.date_utils import safe_to_datetime
  
from scheduler.project_used_resource_manager import ProjectUsedResourceManager
from scheduler.project_scheduler_constants import ACCUMULATED_SYNONYMS, TASK_GOAL, ALL_TAG, USED_RESOURCE_NA, TASK_REMAINING

from utils.logger import create_logger
logger = create_logger(__name__)

class ProjectUsedResourceManagerInitializer:
    """
    Initializes and manages the rows of the 'used resources' DataFrame based on tasks and responsibility information.

    Attributes:
        used_resources_df (pd.DataFrame): DataFrame containing the used resources.
        tasks_df (pd.DataFrame): DataFrame containing the tasks schedule.
        responsible_df (pd.DataFrame): DataFrame containing the responsibility attributes.
        responsible_attr_names (list of str): List of responsibility attribute names.
        date_columns (list of str): List of column names representing date-based resource usage.
        info_columns (list of str): List of column names representing task information attributes.
    """

    def __init__(self, used_resources_df, tasks_df, responsible_df):
        """
        Initializes the ProjectUsedResourceInitializer with the provided DataFrames.

        Args:
            used_resources_df (pd.DataFrame): DataFrame with existing used resources data.
            tasks_df (pd.DataFrame): DataFrame with tasks data (the schedule).
            responsible_df (pd.DataFrame): DataFrame with responsibility data.
        """                
        self.used_resources_df = used_resources_df
        self.tasks_df = tasks_df
        self.responsible_df = responsible_df

        self.responsible_attr_names = list(responsible_df.columns)

        self.date_columns = [col for col in self.used_resources_df.columns if safe_to_datetime(col, errors='coerce') is not pd.NaT]

        for col in self.date_columns:
            self.used_resources_df[col] = self.used_resources_df[col].astype(float)
            
        self.info_columns = [col for col in self.used_resources_df.columns if col not in [TASK_GOAL] + self.responsible_attr_names + self.date_columns]    
                            

    def initialize_used_resource_manager(self):
        """
        Calls methods to add new rows for tasks and responsibilities and initializes all resource columns.

        Returns:
            pd.DataFrame: Updated DataFrame containing the initialized used resources.            
        """
        logger.info("Initializing User Resources Manager... ")

        self._add_new_task_rows()
        self._initialize_resource_columns()

        result = ProjectUsedResourceManager(self.used_resources_df)        

        logger.debug(f"Used Resources DataFrame after initialization:\n{result.used_resources_df}")

        logger.info("User Resources Manager initialized.")

        return result

    def _add_new_task_rows(self):
        """
        Adds new rows to the used resources DataFrame based on tasks and responsibility data.

        - For tasks: Adds rows if the task is not already in the DataFrame.
        - For responsibilities: Adds wildcard rows based on the responsibility DataFrame if not already present.
        """       

        new_rows = []

        # Only tasks with TASK_REMAINING column numeric and > 0
        tasks_to_add = self.tasks_df.copy()        

        tasks_to_add[TASK_REMAINING] = pd.to_numeric(tasks_to_add[TASK_REMAINING], errors='coerce')
        tasks_to_add = tasks_to_add[tasks_to_add[TASK_REMAINING] > 0]
        
        # Add schedule rows
        for _, task in tasks_to_add.iterrows():
            task_data = {TASK_GOAL: task[TASK_GOAL]}
            task_data.update({attr: task[attr] for attr in self.responsible_attr_names})
            
            # Add info columns
            # If AppConfig() has an attribute info_columns_values, it will be used to fill the info columns. Else, it will be filled with the values from the task. 
            if 'infocolumn' in AppConfig():
                task_data.update({attr: AppConfig()["infocolumn"].format_map({"infocolumn":attr}) for attr in self.info_columns})
            else:
                task_data.update({attr: task[attr] for attr in self.info_columns})
            
            """task_data.update({                
                attr: f'=INDEX(T_Schedule[{attr}], MATCH([{TASK_GOAL}], T_Schedule[{TASK_GOAL}], 0),1)'                                
                #attr: '=1+1'
                for attr in self.info_columns
            })"""

            if not ((self.used_resources_df[TASK_GOAL] == task[TASK_GOAL]) &
                    (self.used_resources_df[self.responsible_attr_names] == task[self.responsible_attr_names]).all(axis=1)).any():
                new_rows.append(task_data)
        
        # Add responsibility rows
        for _, row in self.responsible_df.iterrows():
            wildcard_data = {TASK_GOAL: ALL_TAG}
            wildcard_data.update(row.to_dict())
            wildcard_data.update({info: USED_RESOURCE_NA for info in self.info_columns})

            if not ((self.used_resources_df[TASK_GOAL] == ALL_TAG) &
                    (self.used_resources_df[self.responsible_attr_names] == row[self.responsible_attr_names]).all(axis=1)).any():
                new_rows.append(wildcard_data)

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            self.used_resources_df = pd.concat([self.used_resources_df, new_df], ignore_index=True)

    def _initialize_resource_columns(self):
        """
        Initializes the resource usage columns for each row in the used resources DataFrame.

        - For specific tasks: Sets the values to 0 if they are currently NaN.
        - For wildcard rows: Sets values based on the sum of filtered task resources.
        """
        updated_resources = self.used_resources_df

        # Mask for rows not in ACCUMULATED_SYNONYMS
        specific_tasks_mask = ~updated_resources[TASK_GOAL].isin(ACCUMULATED_SYNONYMS)
        wildcard_tasks_mask = updated_resources[TASK_GOAL].isin(ACCUMULATED_SYNONYMS)

        # Apply fillna(0) for specific tasks
        updated_resources.loc[specific_tasks_mask, self.date_columns] = updated_resources.loc[specific_tasks_mask, self.date_columns].fillna(0).infer_objects()

        updated_resources.loc[wildcard_tasks_mask, self.date_columns] = updated_resources[wildcard_tasks_mask].apply(self._calculate_wildcard_resources, axis=1)

        return updated_resources

    def _calculate_wildcard_resources(self, row):
        """
        Calculates the sum of resource usage for rows that match a given responsibility pattern, only filling NaN values.

        Args:
            row (pd.Series): A row representing a wildcard responsibility.

        Returns:
            pd.Series: A Series containing the summed resource usage for each date column.
        """
        responsible_attrs = {attr: row[attr] for attr in self.responsible_attr_names if row[attr] not in ACCUMULATED_SYNONYMS}

        query = ' & '.join([f"{attr} == '{val}'" for attr, val in responsible_attrs.items()])
        
        if query == "":
            filtered_tasks = self.used_resources_df
        else:  
            filtered_tasks = self.used_resources_df.query(query)
        
        calculated_resources = pd.Series(index=self.date_columns)

        for date_col in self.date_columns:
            current_value = row[date_col]
            if pd.isna(current_value) or current_value == USED_RESOURCE_NA:
                calculated_resources[date_col] = filtered_tasks[date_col].sum()
            else:
                calculated_resources[date_col] = current_value

        return calculated_resources