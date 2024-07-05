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

import pandas as pd

from utils.date_utils import safe_to_datetime

from scheduler.project_used_resources_initializer import ProjectUsedResourceManagerInitializer
from scheduler.project_used_resource_manager import ProjectUsedResourceManager
from scheduler.project_scheduler_constants import USED_RESOURCE_GOAL, ACCUMULATED_SYNONYMS

from utils.logger import create_logger
logger = create_logger(__name__)

class ProjectResourceManager:
    """
    Class to manage available and used resources, initializing the used resources and calculating resources per goal.
    """

    def __init__(self, available_resources_df, used_resources_df, tasks_df):
        """
        Initializes the ResourceManager with available and used resources data.

        Args:
            available_resources_df (pd.DataFrame): DataFrame with available resources data.
            used_resources_df (pd.DataFrame): DataFrame with used resources data.
            tasks_df (pd.DataFrame): DataFrame with task information.            

        Raises:
            ValueError: If the columns of responsibility defined in available_resources are missing in `used_resources_df` or 'tasks_df'.
            ValueError: If the date columns in `available_resources_df` do not match those in `used_resources_df`.
        """
        
        self.responsible_attr_names = [
            col for col in available_resources_df.columns
            if col != USED_RESOURCE_GOAL and safe_to_datetime(col, errors='coerce') is pd.NaT
        ]
               
        missing_in_used = [col for col in self.responsible_attr_names if col not in used_resources_df.columns]

        if missing_in_used:
            raise ValueError(f"Missing responsibility columns in used resources: {', '.join(missing_in_used)}")

        missing_in_tasks = [col for col in self.responsible_attr_names if col not in tasks_df.columns]

        if missing_in_tasks:
            raise ValueError(f"Missing responsibility columns in tasks: {', '.join(missing_in_tasks)}")
        
        available_resources_df.columns = [ProjectResourceManager._format_date_column_names(col) for col in available_resources_df.columns]

        used_resources_df.columns = [ProjectResourceManager._format_date_column_names(col) for col in used_resources_df.columns]
        
        available_date_columns = [
            col for col in available_resources_df.columns if safe_to_datetime(col, errors='coerce') is not pd.NaT
        ]

        used_date_columns = [
            col for col in used_resources_df.columns if safe_to_datetime(col, errors='coerce') is not pd.NaT
        ]
    
        if set(available_date_columns) != set(used_date_columns):

            missing_in_available = set(used_date_columns) - set(available_date_columns)
            missing_in_used = set(available_date_columns) - set(used_date_columns)
            
            logger.error("Mismatch between date columns names in available and used resources.")
            
            message = ""
            if missing_in_available:
                message += f"\nUsed date columns not in available: {missing_in_available}"
            if missing_in_used:
                message += f"\nAvailable date columns not in used: {missing_in_used}"

            logger.info(f"{message}")

            raise ValueError(f"Mismatch between date columns names in available and used resources.{message}")
        
        # Convert the values in the columns defined by used_date_columns to float
        for col in used_date_columns:
            used_resources_df[col] = used_resources_df[col].apply(lambda x: float(x) if not pd.isna(pd.to_numeric(x, errors='coerce')) else 0)
            missing_in_used_resources = [col for col in used_date_columns if col not in used_resources_df.columns]

            if missing_in_used_resources:
                raise ValueError(f"Missing date columns in used resources: {', '.join(missing_in_used_resources)}")
        # Convert the values in the columns defined by available_date_columns to float
        for col in available_date_columns:
            available_resources_df[col] = available_resources_df[col].apply(lambda x: float(x) if not pd.isna(pd.to_numeric(x, errors='coerce')) else 0)

        self.available_resources_df = available_resources_df        
        self.responsible_df = available_resources_df[self.responsible_attr_names].drop_duplicates()

        initializer = ProjectUsedResourceManagerInitializer(used_resources_df, tasks_df, self.responsible_df)        
        self.used_resources_manager = initializer.initialize_used_resource_manager()  

    @staticmethod
    def _format_date_column_names(col_name):
        
        date = safe_to_datetime(col_name, errors='coerce')
        
        if pd.notna(date):            
            return date.strftime('%d/%m/%Y')
        else:                
            return col_name


    def clean_resources(self, clean_date):
        """
        Cleans the used resources for dates after a specific date.

        Args:
            clean_date (datetime): The date after which to clean the used resources.
        """
        self.used_resources_manager.clean_used_resources(clean_date)

        logger.info("Resources cleaned for dates after: %s", clean_date.strftime('%d/%m/%Y'))

    def obtain_goal_resources(self, current_date, **filters):
        """
        Calculate the resources available for a specific goal and date, considering wildcards.

        Args:
            current_date (str): The date column for which to obtain available resources.
            **filters (dict): Dynamic filter values to apply, should include the columns defined in available resources.

        Returns:
            float: The minimum available resources after accounting for usage.

        Raises:
            ValueError: If the date column is missing or if required filters are not provided.
        """        
        if current_date not in self.available_resources_df.columns or safe_to_datetime(current_date, errors='coerce') is pd.NaT:
            raise ValueError(f"Invalid or missing date column: {current_date}")

        valid_columns = self.responsible_attr_names
        missing_filters = [col for col in valid_columns if col not in filters]

        if missing_filters:
            raise ValueError(f"Missing required filters: {', '.join(missing_filters)}")

        # Remove any extra columns from filters
        filters = {k: v for k, v in filters.items() if k in valid_columns}

        # Filter the available resources DataFrame using filters
        # Wildcards are not relevant here.
        
        mask = pd.Series(True, index=self.available_resources_df.index)
        
        for col, val in filters.items():
            if col not in self.available_resources_df.columns:
                raise ValueError(f"Invalid or nonexistent column: {col}")
            # Apply wildcard filtering directly with boolean indexing
            mask &= (self.available_resources_df[col].isin(ACCUMULATED_SYNONYMS)) | (self.available_resources_df[col] == val)

        filtered_df = self.available_resources_df.loc[mask]
        
        if filtered_df.empty:
            return 0

        remaining_resources = float('inf')
        
        # Aggregate remaining resources
        def calculate_remaining(row):
            responsibility_filters = {col: row[col] for col in self.responsible_attr_names + [USED_RESOURCE_GOAL]}
            available = row[current_date]
            used = self.used_resources_manager.obtain_used_goal_resources(current_date, **responsibility_filters)
            return available - used

        remaining_resources = filtered_df.apply(calculate_remaining, axis=1).min()

        return max(remaining_resources, 0)  # Ensure no negative values
    
    def update_goal_resources (self, current_date, resources_used, **goal_filter):

        logger.debug(f"Updating resources for date {current_date} and goal {goal_filter}")

        filter_keys = self.responsible_attr_names + [USED_RESOURCE_GOAL]

        responsible_filter = {key: goal_filter[key] for key in filter_keys if key in goal_filter}
        
        self.used_resources_manager.update_used_resources(current_date, resources_used, True, **responsible_filter)

        logger.debug(f"Resources updated for date {current_date} and goal {goal_filter}")

    def get_dayfirst(self):
        return self.__class__.DAYFIRST