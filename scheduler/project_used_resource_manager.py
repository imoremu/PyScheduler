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

import re
import pandas as pd
from datetime import datetime

from utils.date_utils import safe_to_datetime
from utils.app_config import AppConfig

from scheduler.project_scheduler_constants import ACCUMULATED_SYNONYMS

from utils.logger import create_logger
logger = create_logger(__name__) 

class ProjectUsedResourceManager:
    """ 
    Class to manage the used resources for a project, updating the used resources DataFrame with the resources allocated to tasks.

    This class allows the user to update the used resources DataFrame with the resources allocated to tasks, considering the date and filters provided.

    Attributes:
        used_resources_df (pd.DataFrame): DataFrame containing the used resources with specific columns for dates and other categories such as team or project.
    """ 
    
    def __init__(self, used_resources_df):        
        """
        Initializes the manager with a DataFrame containing the used resources.

        Used Resources: This DataFrame includes resources used on each date for each task or responsibility group (if the date is in the past), or indicates the estimated resources consumed (if the date is in the future).
        It consists of the following types of columns:
        - Responsibility columns: Define the resource responsibility. These columns will be defined by the library user. E.g. [Team, Project, Area, SubArea, Responsible]
        User Resources could have more or fewer columns depending on their organization or even different ones with different names. 
        Responsibility columns accept regexp or * in their columns for managing resources groups.
        - Task ID column: Can be the task ID for resources allocated by task, or * for resources used on a date by a responsibility team.
        - Task information columns: References the Schedule table to obtain additional information and make it easier to use.
        - Date columns: Where the resources used for each task or team are included on a given date.

        Args:
            used_resources_df (pd.DataFrame): DataFrame containing the used resources with specific columns for dates and other categories such as team or project.
        """        
        self.used_resources_df = used_resources_df.fillna(0)              
        
    
    def clean_used_resources(self, clean_date):
        """
        Cleans the values of the used resource columns corresponding to future dates from the specified date.

        This method resets to zero all the values in date columns that are later than the provided 'clean_date',
        preparing the used resources DataFrame for a new resource assignment process without previously calculated
        values that might be outdated or incorrect.

        Args:
            clean_date (str or datetime): The date from which future used resources should be cleaned. This date can be a string or a datetime object.
                                          If it's a string, the expected format can be adjusted using the 'dayfirst' parameter.
            dayfirst (bool): Indicates whether the first element of the date is the day (True) or the month (False). Default is True, useful for common formats outside the US, like DD/MM/YYYY.

        Returns:
            None: This method does not return any values. It modifies the 'used_resources_df' DataFrame in-place.

        Examples:
            # Example with date string
            manager.clean_used_resources('15/10/2024')

            # Example with datetime object
            from datetime import datetime
            manager.clean_used_resources(datetime(2024, 10, 15))
        """
        if isinstance(clean_date, str):
            clean_date = safe_to_datetime(clean_date)
        
        date_columns = [col for col in self.used_resources_df.columns if safe_to_datetime(col, errors='coerce') is not pd.NaT]
        
        future_dates = [date for date in date_columns if safe_to_datetime(date) >= clean_date]

        for date in future_dates:
            self.used_resources_df[date] = 0.0

        logger.info("Resources cleaned for dates after: %s", clean_date.strftime('%d/%m/%Y'))


    def obtain_used_goal_resources(self, date, **filter_conditions):
        """
        Retrieves the used resources for a given date and specific filters. Note: '*' are treated as actual values, not wildcards.

        Args:
            date (str): Date for which to obtain the used resources.
            **filter_conditions (dict): Filters to apply on the DataFrame columns.

        Returns:
            int: Sum of used resources for the given date and filters.

        Raises:
            ValueError: If the date column is invalid or does not exist.
        """
        if date not in self.used_resources_df.columns or safe_to_datetime(date, errors='coerce') is pd.NaT:
            raise ValueError(f"The date column {date} is not valid or does not exist in the Used Resources DataFrame.")
        
        filtered_df = self.used_resources_df

        for col, val in filter_conditions.items():
            if val in ACCUMULATED_SYNONYMS:                                        
                filtered_df = filtered_df[filtered_df[col].isin(ACCUMULATED_SYNONYMS)]
            else:
                filtered_df = filtered_df[filtered_df[col] == val]

        used_resources = filtered_df[date].sum()

        return used_resources
        
    def update_used_resources(self, current_date, resources_used, increase = True, **filters):
        """
        Updates the used resources for a given date, considering regexp in the DataFrame rows. All the resources rows that matches the passed filter, will be updated.

        Args:
            date (str): Date column in which to update the resources.
            resources_used (float): Amount of resources to update.
            increase (bool): If True, the resources are added; if False, the value is set. Default: True
            **filters (dict): Filters defining which rows to update. '*' values in the DataFrame act as wildcards.

        Raises:
            ValueError: If the date column is invalid or does not exist.
        """
        logger.debug("Updating used resources for date %s", current_date)

        if current_date not in self.used_resources_df.columns:
            logger.error("The date column %s is not valid or does not exist in the Used Resources DataFrame.", current_date)
            raise ValueError(f"The date column {current_date} is not valid or does not exist in the Used Resources DataFrame.")

        mask = pd.Series(True, index=self.used_resources_df.index)

        def is_valid_regex(pattern):
            try:
                re.compile(str(pattern))
                return True
            except:
                return False
        
        def match_regex(pattern, value):
            
            return pattern in ACCUMULATED_SYNONYMS or value == pattern or (is_valid_regex(str(pattern)) and bool(re.match(str(pattern), value)))

        for key, value in filters.items():
            if key not in self.used_resources_df.columns:
                logger.error("The column %s is not valid or does not exist in the Used Resources DataFrame.", key)
                raise ValueError(f"The column {key} is not valid or does not exist in the Used Resources DataFrame.")
            
            mask &= self.used_resources_df[key].apply(lambda x: match_regex(x, value))
            
        if increase:                                        
                self.used_resources_df.loc[mask, current_date] += resources_used
        else:
            self.used_resources_df.loc[mask, current_date] = resources_used

        logger.debug("Resources updated successfully.") 