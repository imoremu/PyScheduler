Feature: Update Excel Schedule

  Scenario: Plan two tasks with the same priority
    Given an Excel file with tasks having the same priority
    When I update the task schedule in the Excel file with value
    Then the tasks should be planned with the same end date

  Scenario: Plan tasks with different priorities
    Given an Excel file with tasks having different priorities
    When I update the task schedule in the Excel file with value
    Then the task with the higher priority should be planned first

  Scenario: Task blocking another task
    Given an Excel file with tasks where one task blocks the start of another
    When I update the task schedule in the Excel file with value
    Then the blocked task should not start until the blocking task is complete

  Scenario: Task with a date restriction
    Given an Excel file with tasks where one task has a start date restriction
    When I update the task schedule in the Excel file with value
    Then the task should not start until the given start date

  Scenario: Used Resource Info Column With Excel Formula
    Given an Excel file with tasks where one task has a start date restriction
    When I update the task schedule in the Excel file with formula
    Then the Info Column should be filled with the correct Excel formulas

  Scenario: Used Resource Info Column With Value
    Given an Excel file with tasks where one task has a start date restriction
    When I update the task schedule in the Excel file with value
    Then the Info Column should be filled with the correct value