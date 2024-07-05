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

import json
import numpy as np
import pandas as pd
import datetime

from utils.date_utils import safe_to_datetime

from utils.logger import create_logger
logger = create_logger(__name__) 

from utils.util_constants import CONF_HOLIDAYS
from utils.app_config import AppConfig

from scheduler.project_scheduler_constants import (
    TASK_AUX_ALLOCATABLE_RESOURCES, TASK_AUX_RESPONSIBILITY_DICT, TASK_BLOCKED_DAYS, TASK_ID, TASK_PRIORITY, TASK_RESOURCES_MAX, 
    TASK_RESTRICTION, TASK_REMAINING, TASK_START_DATE, TASK_END_DATE, TASK_AUX_WEIGHT, TASK_AUX_RESPONSIBILITY_KEY, TASK_GOAL
)

class TaskManager:
    """
    TaskManager coordinates and updates the task schedule based on available resources.

    Tasks have three types of columns:

    - Task identification column: ID
    - Responsibility columns: Define those responsible for a task. These columns will be defined by the user. E.g. [Team, Project, Area, SubArea, Responsible]
      A user may have more or fewer columns depending on their organization, or even different ones with different names. 
      Responsibility columns accept regexp or * in their columns, allowing different responsibles to cover it.

      E.g.: Team = .*. or just * on tasks definition means that this task can be done by a member of any Team

    - Task planning columns: These are fixed for all users and include: priority, remaining, constraint dates, and maximum resources allocated to the task.
    - Task information columns: These are defined by the user. For instance: task type, associated product, tags, difficulty, risks, notes...

    Available Resources has two types of columns:
    - Responsibility columns: These are the same as those in the Schedule. 
      They accept also regexp or *, but instead of defining who can perform the task, as in the task dataframe, it defines what the responsible can do.      

      E.g.: Team = .*. or just * on available resources means that this resource is able to perform tasks of any Team

    - Date columns: Indicate the resources available on a given date for a responsible team.


    """
    
    AVAILABLE_RESOURCES = "Available Resources"
    
    def __init__(self, tasks_df, resource_manager, period_days_available = 5):
        """
        Initialize the TaskManager with the task data and resource manager.

        Args:
            tasks_df (pd.DataFrame): DataFrame containing the task schedule. 
            resource_manager (ProjectResourceManager): An initialized resource manager instance.
            period_days_available (int): Number of days to consider for the available resources. Default is 5 days.

        Raises:
            ValueError: If any required column is missing from the tasks DataFrame.
        """                        
        logger.info("Initializing TaskManager...")
        logger.debug(f"Tasks DataFrame: {tasks_df}")

        self.tasks_df = tasks_df
        self.resource_manager = resource_manager
        self.period_days_available = period_days_available
                   
        # Define the columns that are required
        required_columns = [TASK_PRIORITY, TASK_REMAINING, TASK_ID, TASK_GOAL, TASK_RESOURCES_MAX]

        responsible_attr_names = resource_manager.responsible_attr_names        
        required_columns.extend(responsible_attr_names)
        
        # If TASK_ID column existes and has numeric type, turn them strings        
        if TASK_ID in tasks_df and (tasks_df[TASK_ID].dtype == np.int64 or tasks_df[TASK_ID].dtype == np.float64):
            tasks_df[TASK_ID] = tasks_df[TASK_ID].astype(str)                

        if TASK_RESTRICTION not in tasks_df.columns or tasks_df[TASK_RESTRICTION].isnull().all():
            self.tasks_df[TASK_RESTRICTION] = None
            logger.info(f"Column {TASK_RESTRICTION} missing. Initialized with default value None.")
        else:
            self.tasks_df[TASK_RESTRICTION] = self.tasks_df[TASK_RESTRICTION].replace('', np.nan)
            self.tasks_df[TASK_RESTRICTION] = self.tasks_df[TASK_RESTRICTION].apply(
                lambda x: safe_to_datetime(x, errors="ignore") if pd.notnull(x) else x)

        # Initialize TASK_RESOURCES_MAX with default values if missing or invalid
        if TASK_RESOURCES_MAX not in tasks_df.columns or tasks_df[TASK_RESOURCES_MAX].isnull().all():
            self.tasks_df[TASK_RESOURCES_MAX] = float('inf')
            logger.info(f"Column {TASK_RESOURCES_MAX} missing. Initialized with default value infinity.")
        else:
            self.tasks_df[TASK_RESOURCES_MAX] = self.tasks_df[TASK_RESOURCES_MAX].replace('', np.nan)
            self.tasks_df[TASK_RESOURCES_MAX] = pd.to_numeric(self.tasks_df[TASK_RESOURCES_MAX], errors='coerce').fillna(float('inf'))
        
        # Fill TASK_BLOCKED_DAYS with 0 if missing or invalid
        if TASK_BLOCKED_DAYS not in tasks_df.columns:
            self.tasks_df[TASK_BLOCKED_DAYS] = 0
            logger.info(f"Column {TASK_BLOCKED_DAYS} missing. Initialized with default value 0.")
        else:
            self.tasks_df[TASK_BLOCKED_DAYS] = self.tasks_df[TASK_BLOCKED_DAYS].replace('', np.nan)
            self.tasks_df[TASK_BLOCKED_DAYS] = pd.to_numeric(self.tasks_df[TASK_BLOCKED_DAYS], errors='coerce').fillna(0)        

        TaskManager.check_task_schedule(self.tasks_df, required_columns)
        
        self.tasks_df[TASK_REMAINING] = self.tasks_df[TASK_REMAINING].replace('N/A', np.nan)
        self.tasks_df[TASK_REMAINING] = pd.to_numeric(self.tasks_df[TASK_REMAINING], errors='coerce').fillna(0)        

        # Clean End Dates
        TaskManager.clean_end_dates(self.tasks_df)        

        # Create responsibility column to improve performance when comparing responsibilities or grouping by responsibility
        self.tasks_df[TASK_AUX_RESPONSIBILITY_KEY] = self.tasks_df.apply(
            TaskManager.generate_responsibility_key, axis=1, responsible_columns=responsible_attr_names)
        
        self.tasks_df[TASK_AUX_RESPONSIBILITY_DICT] = self.tasks_df.apply(
            TaskManager.generate_responsibility_dict, axis=1,responsible_columns=responsible_attr_names )

        self.tasks_df.sort_values(by=TASK_PRIORITY, inplace=True)
        logger.info("TaskManager initialized successfully with all required columns.")

    @staticmethod
    def is_number(n):
        try:
            float_n = float(n)
        except ValueError:
            return False
        else:
            return True


    @staticmethod
    def check_task_schedule(tasks_df, required_columns = None):
        """
        Check the task schedule for inconsistencies. It includes:

        - Negative values
        - Missing values (ID, Goal, Responsibility, Priority, Remaining)
        - Invalid values (string on numeric columns)
        - Duplicated Ids
        - Duplicated Goals
        
        Raises:
            ValueError: If any of the above inconsistencies are found.
        """
        logger.info("Checking task schedule...")

        if required_columns:
            # Verify that all required columns are present in the tasks DataFrame
            missing_columns = [col for col in required_columns if col not in tasks_df.columns]
            if missing_columns:
                logger.error(f"Missing required column(s): \n {'\n'.join(missing_columns)}")
                raise ValueError(f"Missing required column(s): \n {'\n'.join(missing_columns)}")
                    
        # Check for missing values in ID or Goal
        missing_values = tasks_df[tasks_df[TASK_ID] == ''][TASK_ID].tolist()
       
        if missing_values:
            logger.error(f"Missing values found in ID Column in task schedule: \n {'\n'.join(missing_values)}")
            raise ValueError(f"Missing values found in ID Column in task schedule: \n {'\n'.join(missing_values)}")

        missing_values = tasks_df[tasks_df[TASK_GOAL] == ''][TASK_ID].tolist()

        if missing_values:
            logger.error(f"Missing values found in Goal Column in task schedule: \n {'\n'.join(missing_values)}")
            raise ValueError(f"Missing values found in Goal Column task schedule: \n {'\n'.join(missing_values)}")

        missing_values = tasks_df[str(tasks_df[TASK_REMAINING]) == '' or tasks_df[TASK_REMAINING].isnull()][TASK_ID].tolist()

        if missing_values:
            logger.warn(f"Tasks with remaining work empty: \n {'\n'.join(str(missing_values))}")     
            # In this case no exception is raised, as it is not an error, but a warning.
                
        # Check for duplicated IDs
        duplicated_ids = tasks_df[tasks_df.duplicated(subset=TASK_ID, keep=False)][TASK_ID].tolist()

        if duplicated_ids:
            logger.error(f"Duplicated IDs found in task schedule: \n {'\n'.join(duplicated_ids)}")
            raise ValueError(f"Duplicated IDs found in task schedule: \n {'\n'.join(duplicated_ids)}")
        
        duplicated_goals = tasks_df[tasks_df.duplicated(subset=TASK_GOAL, keep=False)][TASK_GOAL].tolist()

        if duplicated_goals:
            logger.error(f"Duplicated Goals found in task schedule: \n {'\n'.join(duplicated_goals)}")
            raise ValueError(f"Duplicated Goals found in task schedule: \n {'\n'.join(duplicated_goals)}")
        
        # Check for invalid values
        # log all TASK_ID for all task with remaining not numeric, neither empty neither 'N/A'        
        invalid_task_ids = tasks_df[tasks_df[TASK_REMAINING].apply(lambda x: not pd.isnull(x) and not TaskManager.is_number(str(x)) and not str(x) == 'N/A')][TASK_ID].tolist()
                
        if invalid_task_ids:
            logger.error(f"Invalid values found in task remaining: \n {'\n'.join(invalid_task_ids)}")
            raise ValueError(f"Invalid values found in task remaining: \n {'\n'.join(invalid_task_ids)}")                        

        # Invalid values in TASK_RESOURCES_MAX (not numeric, neither empty, neither 'N/A', neither inf)
        invalid_task_ids = tasks_df[tasks_df[TASK_RESOURCES_MAX].apply(lambda x: not pd.isnull(x) and not str(x) == "" and not TaskManager.is_number(str(x)) and x != float('inf'))][TASK_ID].tolist()

        if invalid_task_ids:
            logger.error(f"Invalid values found in task resources max: \n {'\n'.join(invalid_task_ids)}")
            raise ValueError(f"Invalid values found in task resources max: \n {'\n'.join(invalid_task_ids)}")
        
        # Invalid values in TASK_PRIORITY
        invalid_task_ids = tasks_df[tasks_df[TASK_PRIORITY].apply(lambda x: not pd.isnull(x) and not TaskManager.is_number(str(x)) and str(x) != 'N/A')][TASK_ID].tolist()

        if invalid_task_ids:
            logger.error(f"Invalid values found in task priority: \n {'\n'.join(invalid_task_ids)}")
            raise ValueError(f"Invalid values found in task priority: \n {'\n'.join(invalid_task_ids)}")            

        # Check for negative values
        # Negative values in Remaining or Resources Max or Priority
        invalid_task_ids = tasks_df[tasks_df[TASK_REMAINING].apply(lambda x: not pd.isnull(x) and str(x) != 'N/A' and TaskManager.is_number(str(x)) and x < 0)][TASK_ID].tolist()
        
        if invalid_task_ids:
            logger.error(f"Negative values found in task remaining: \n {'\n'.join(invalid_task_ids)}")
            raise ValueError(f"Negative values found in task remaining: \n {'\n'.join(invalid_task_ids)}")
        
        invalid_task_ids = tasks_df[tasks_df[TASK_RESOURCES_MAX].apply(lambda x: not pd.isnull(x) and str(x) != 'N/A' and TaskManager.is_number(str(x)) and str(x) != 'N/A' and x < 0)][TASK_ID].tolist()

        if invalid_task_ids:
            logger.error(f"Negative values found in task resources max: \n {'\n'.join(invalid_task_ids)}")
            raise ValueError(f"Negative values found in task resources max: \n {'\n'.join(invalid_task_ids)}")
        
        invalid_task_ids = tasks_df[tasks_df[TASK_PRIORITY].apply(lambda x: str(x) != 'N/A' and TaskManager.is_number(str(x)) and x < 0)][TASK_ID].tolist()

        if invalid_task_ids:
            logger.error(f"Negative values found in task priority: \n {'\n'.join(invalid_task_ids)}")
            raise ValueError(f"Negative values found in task priority: \n {'\n'.join(invalid_task_ids)}")
                    
        logger.info("Task schedule check completed successfully.")

    def update_task_schedule(self, dates):
        """
        Update the task schedule based on available resources, following restrictions and priority.

        Args:
            dates ([str]): Dates (as defined in the resource_manager) to be processed             

        Returns:
            pd.DataFrame: Updated tasks DataFrame with updated start and end dates and adjusted resources.
        """
        logger.info("Updating task schedule...")

        # Clean used resources for dates after today
        self.resource_manager.clean_resources(datetime.datetime.now())

        grouped = self.tasks_df.groupby([TASK_PRIORITY, TASK_AUX_RESPONSIBILITY_KEY])

        for current_date in dates:            

            logger.info(f"Processing tasks for date: {current_date}")

            # Continue if date is before today
            if safe_to_datetime(current_date, errors='coerce') < datetime.datetime.now():
                continue          
            
            for (priority, resp_key), tasks in grouped:
                # Completed tasks calcualted inside the loop to get possible tasks finished with lower priority
                # Problem: task blocked by task with lower priority will be planned one period later
                # Blocked taks should have always less priority
                completed_tasks = self.tasks_df[self.tasks_df[TASK_REMAINING] == 0][TASK_ID].tolist()

                filtered_tasks = TaskManager.filter_tasks_by_restriction(tasks, completed_tasks, current_date)

                if filtered_tasks.empty:
                    continue
                
                logger.debug(f"Processing tasks for priority {priority} and responsibility key {resp_key}")                
            
                resp_dict = filtered_tasks.iloc[0][TASK_AUX_RESPONSIBILITY_DICT]

                available_effort = self.resource_manager.obtain_goal_resources(current_date, **resp_dict) * self.period_days_available         

                if available_effort == 0:                                           
                    continue

                filtered_tasks = TaskManager._distribute_resources_same_priority_and_responsible_tasks(filtered_tasks, available_effort, self.period_days_available)

                filtered_tasks = filtered_tasks.apply(lambda task: self.allocate_resources(task, task[TASK_AUX_ALLOCATABLE_RESOURCES], current_date), axis=1)

                logger.debug(f"Tasks allocated for date {current_date}.")

                # Update the original DataFrame with changes
                self.tasks_df.update(filtered_tasks)

        logger.info("Task schedule update completed.")
        return self.tasks_df
    
    @staticmethod
    def _distribute_resources_same_priority_and_responsible_tasks(tasks, available_effort, period_days_available = 5):
        """
        Distribute available resources among tasks of the same priority based on their remaining work, 
        resource limits, and resources already used, specifically for tasks of the same priority
        and responsibility.

        This method iteratively allocates resources to tasks until no more resources can be distributed.
        The allocation considers the maximum resources available, maximum resources per task, and
        remaining work for each task. It ensures that tasks are proportionally allocated resources based on
        their remaining needs.

        Args:
            tasks (pd.DataFrame): DataFrame of tasks at the same priority and responsibility key.
            available_effort (float): The total available effort for the tasks.
            period_days_available (int): Number of days to consider for the available resources. Default is 5 days.

        Returns:
            pd.DataFrame: The updated tasks DataFrame with allocated resources noted.
        """
        max_available = available_effort
        
        if max_available == 0:
            tasks[TASK_AUX_ALLOCATABLE_RESOURCES] = 0            
            return tasks

        results = pd.DataFrame()
        
        logger.debug(f"Allocating resources for {tasks.shape[0]} tasks with {max_available} resources available.")

        while not tasks.empty:
            if tasks.shape[0] == 1:
                first_task = tasks.iloc[0]                                
                
                logger.debug(f"Allocating {min(first_task[TASK_RESOURCES_MAX], max_available, first_task[TASK_REMAINING])} resources for task {first_task[TASK_ID]}.")

                allocatable_resources = min(first_task[TASK_RESOURCES_MAX] * period_days_available, max_available, first_task[TASK_REMAINING])
                tasks[TASK_AUX_ALLOCATABLE_RESOURCES] = allocatable_resources
                results = pd.concat([results, tasks])
                break
            
            logger.debug("Tasks before allocation:")
            logger.debug(f"Tasks: {tasks[TASK_ID].tolist()}")     
            logger.debug(f"Period: {period_days_available} days")                   
            logger.debug(f"Resources maximum (per period): {tasks[TASK_RESOURCES_MAX].tolist()} (*resources per period*)")
            logger.debug(f"Resources remaining: {tasks[TASK_REMAINING].tolist()} (*days*)")             

            tasks[TASK_AUX_WEIGHT] = tasks[TASK_REMAINING] / tasks[TASK_REMAINING].sum()

            logger.debug(f"Calculated Weight: {tasks[TASK_AUX_WEIGHT].tolist()}")               

            tasks[TASK_AUX_ALLOCATABLE_RESOURCES] = tasks.apply(
                lambda task: min(max_available * task[TASK_AUX_WEIGHT], task[TASK_RESOURCES_MAX] * period_days_available, task[TASK_REMAINING]), axis=1
            )

            logger.debug(f"Calculated Allocatable Resources: {tasks[TASK_AUX_ALLOCATABLE_RESOURCES].tolist()}")

            fully_allocated_mask = tasks[TASK_AUX_ALLOCATABLE_RESOURCES] < (tasks[TASK_AUX_WEIGHT] * max_available)
            max_available -= tasks[fully_allocated_mask][TASK_AUX_ALLOCATABLE_RESOURCES].sum()

            fully_allocated_tasks = tasks[fully_allocated_mask]
            if fully_allocated_tasks.empty:
                results = pd.concat([results, tasks])
                break
            
            results = pd.concat([results, fully_allocated_tasks])

            tasks = tasks[~fully_allocated_mask]
        return results
                    
            
    def allocate_resources(self, task, available_effort, current_date): 
        """
        Allocate resources for a specific task on a given date.

        Args:
            task (pd.Series): The task for which resources are being allocated.
            available_effort (float): The total available effort for the task.
            current_date (str): The date for which resources are being allocated.
        """        
        self.update_task_attributes(task, available_effort, current_date)        
        self.resource_manager.update_goal_resources(current_date, available_effort / 5, **task)

        return task

    @staticmethod
    def update_task_attributes(task, available_effort, current_date):
        """
        Allocate resources for a specific task on a given date.
        
        Args:
            task (pd.Series): The task for which resources are being allocated.
            available_effort (float): The total available effort for the task.
            current_date (str): The date for which resources are being allocated.
        
        Returns:
            pd.Series: The updated task with modified resource allocation.
        """                                        
        logger.debug(f"Allocating {available_effort} resources for task {task[TASK_ID]} on {current_date}.")

        task[TASK_REMAINING] -= available_effort

        if pd.isna(task.get(TASK_START_DATE)):
            task[TASK_START_DATE] = current_date

        if task[TASK_REMAINING] <= 0:
            task[TASK_REMAINING] = 0
            
            holidays = AppConfig()[CONF_HOLIDAYS] if CONF_HOLIDAYS in AppConfig() else []
            
            if TASK_END_DATE not in task or pd.isnull(task[TASK_END_DATE]):         
                if TASK_BLOCKED_DAYS in task and task[TASK_BLOCKED_DAYS] > 0:
                    end_date = TaskManager.calculate_end_date_with_block(current_date, task[TASK_BLOCKED_DAYS], holidays)
                    task[TASK_END_DATE] = end_date
                else:
                    task[TASK_END_DATE] = current_date                   

        end_date = task[TASK_END_DATE] if TASK_END_DATE in task else "N/D"
        start_date = task[TASK_START_DATE] if TASK_START_DATE in task else "N/D"

        logger.debug(f"Task {task[TASK_ID]} updated. Remaining: {task[TASK_REMAINING]} Start: {start_date} End: {end_date}")

    @staticmethod
    def filter_tasks_by_restriction(tasks_df, completed_tasks, current_date):
        """
        Filters tasks based on their restrictions.

        Args:
            tasks_df (pd.DataFrame): The DataFrame containing the task schedule.        
            completed_tasks (list): A list of task IDs that are already complete.
            current_date (datetime): The current date being processed.
            
        Returns:
            pd.DataFrame: Filtered DataFrame containing only tasks that are ready for processing.
        """
        
        logger.debug(f"Filtering tasks for date {current_date}")
        
        if isinstance(current_date, str):
            current_date = safe_to_datetime(current_date)

        elif isinstance(current_date, datetime.date):
            current_date = safe_to_datetime(current_date)
        
        mask = tasks_df[TASK_RESTRICTION].isna()
        mask |= (tasks_df[TASK_RESTRICTION].isin(completed_tasks))
        mask |= (safe_to_datetime(tasks_df[TASK_RESTRICTION], errors='coerce')) <= current_date
        mask &= ~tasks_df[TASK_ID].isin(completed_tasks)

        return tasks_df[mask]

    @staticmethod
    def generate_responsibility_key(row, responsible_columns):
        """Generates a JSON string based on the values in responsible columns."""        
        return json.dumps(TaskManager.generate_responsibility_dict(row, responsible_columns))
    
    @staticmethod
    def generate_responsibility_dict(row, responsible_columns):
        """Generates a dictionary based on the values in responsible columns."""
        responsibility_dict = {col: row[col].item() if hasattr(row[col], 'item') else row[col] for col in responsible_columns}
        return responsibility_dict

    @staticmethod
    def clean_end_dates(tasks):        
        """Remove end dates for tasks with remaining work > 0."""
        mask = tasks[TASK_REMAINING] > 0
        tasks.loc[mask, TASK_END_DATE] = None       

    @staticmethod
    def calculate_end_date_with_block(start_date, block_days, holidays = []):
        """
        Calculates the end date considering blocked days, excluding weekends and holidays.

        Args:
            start_date (datetime.date or str): The date from which to start counting.
            block_days (int): Number of business days to block.
            holidays (list of datetime.date or str): Dates that are holidays.

        Returns:
            datetime.date: The calculated end date.
        """
        current_date = safe_to_datetime(start_date).date()
        days_added = 0

        while days_added < block_days:
            current_date += datetime.timedelta(days=1)
            if current_date.weekday() < 5 and current_date not in holidays:
                days_after_increment = current_date.weekday()
                if days_after_increment < 5:
                    days_added += 1

        return current_date