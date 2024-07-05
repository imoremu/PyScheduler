Private schedule_sheet As Worksheet
Private schedule_header As ListObject

Private available_resources_sheet As Worksheet
Private available_resources_header As ListObject

Private used_resources_sheet As Worksheet
Private used_resources_header As ListObject

Private date_sheet As Worksheet

Private project_resources As ProjectResources

Private priority_column As Integer

Private id_column As Integer
    
Private remaining_column As Integer
   
Private goal_column As Integer
    
Private project_column As Integer

Private product_column As Integer
    
Private team_column As Integer

Private group_column As Integer

Private resource_max_column As Integer

Private responsible_column As Integer
    
Private version_column As Integer

Private cp_column As Integer
       
Private name_column As Integer
        
Private start_date_column As Integer
       
Private end_date_column As Integer

Private work_column As Integer

Private restriction_date_column As Integer

Private blocked_days_column As Integer

Private tasks As Dictionary

Private easter_sundays As Dictionary

Private new_start_dates() As Variant
Private new_end_dates() As Variant


Sub init(schedule_sheet_in As Worksheet, available_resources_sheet_in As Worksheet, used_resources_sheet_in As Worksheet, date_sheet_in As Worksheet)
    
    Set schedule_sheet = schedule_sheet_in
    Set schedule_header = schedule_sheet.ListObjects(1)
    
    Set available_resources_sheet = available_resources_sheet_in
 
    Set used_resources_sheet = used_resources_sheet_in
    
    Set date_sheet = date_sheet_in
    
    Set project_resources = New ProjectResources
    
    project_resources.init available_resources_sheet, used_resources_sheet
                      
    init_column_numbers
    
    rows_count = schedule_header.ListRows.Count
    
    ReDim new_start_dates(1 To rows_count, 1 To 1)
    ReDim new_end_dates(1 To rows_count, 1 To 1)
    
End Sub
Private Sub init_column_numbers()
              
    priority_column = schedule_header.ListColumns("Priority").Index
    id_column = schedule_header.ListColumns("Id").Index
    remaining_column = schedule_header.ListColumns("Remaining").Index
    goal_column = schedule_header.ListColumns("Goal").Index
    project_column = schedule_header.ListColumns("Project").Index
    product_column = schedule_header.ListColumns("Product").Index
    team_column = schedule_header.ListColumns("Team").Index
    group_column = schedule_header.ListColumns("Group").Index
    responsible_column = schedule_header.ListColumns("Responsible").Index
    version_column = schedule_header.ListColumns("Version").Index
    cp_column = schedule_header.ListColumns("CP").Index
    name_column = schedule_header.ListColumns("Name").Index
    start_date_column = schedule_header.ListColumns("Start Date").Index
    end_date_column = schedule_header.ListColumns("End Date").Index
    work_column = schedule_header.ListColumns("Work").Index
    resource_max_column = schedule_header.ListColumns("Resources Max.").Index
    restriction_date_column = schedule_header.ListColumns("Restriction").Index
    
    Rem Optional Columns
    
    On Error Resume Next
    
    blocked_days_column = 0
    blocked_days_column = schedule_header.ListColumns("Blocked Days").Index
    
    On Error GoTo 0

End Sub

Sub update_schedule()

    Dim available_resources_column As Range
   
    Dim current_date As Date
    
    Dim clean_date As Date
    
    Dim schedule_ok As Boolean
    
    Dim t_schedule As ListObject
    Dim sort_column As Range
    
    If schedule_sheet.FilterMode = True Then
            schedule_sheet.ShowAllData
    End If
    
    Set t_schedule = schedule_sheet.ListObjects("T_Schedule")
    Set sort_column = Range("T_Schedule[Priority]")
    
    With t_schedule.Sort
        .SortFields.Clear
        .SortFields.Add key:=sort_column, SortOn:=xlSortOnValues, Order:=xlAscending
        .Header = xlYes
        .Apply
    End With
                   
    Application.StatusBar = "Chequeando schedule"
    
    Set tasks = New Dictionary
    Set easter_sundays = New Dictionary
    
    schedule_ok = check_schedule_ok()
    
    If schedule_ok Then
        
        day_total_resources = 0
                                               
        Application.StatusBar = "Calculando Fechas"
        
        Rem If Not IsNull(date_sheet) Then
        Rem    clean_date = date_sheet.Cells(3, 2).Value
                            
        Rem    If clean_date < Date Then
        clean_date = Date
        Rem    End If
        Rem Else
        Rem clean_date = Date
        Rem End If
            
        project_resources.Clean_Used_Resources (clean_date)
            
        For Each available_resources_column In available_resources_sheet.UsedRange.Columns
                                   
            If available_resources_column.Column > 5 Then
                       
                current_date = available_resources_column.Cells(1, 1)
                                                            
                If (current_date > clean_date) Then
                                    
                    If WorksheetFunction.NetworkDays_Intl(current_date, current_date) = 1 Then
                       Application.StatusBar = Format(current_date, "Short Date")
                       
                       project_resources.update_day available_resources_column.Column, current_date
                                        
                       Day_Schedule_Update_From_Resources current_date
                        
                    End If
                        
                End If
                                                                                                                                                                                       
            End If
                    
        Next
        
        project_resources.update_sheet
        
        analyze_date_changes
    
        Application.StatusBar = ""
    
        MsgBox ("Update Finished. See 'Last Changes' Sheet for more information")
    
    End If

End Sub

Function check_schedule_ok() As Boolean

    Dim id As String
    Dim remaining As Double
    
    Dim goal_name As String
    
    Dim project_name As String
    Dim product_name As String
    
    Dim team_name As String
    Dim group_name As String
    
    Dim version_name As String
      
    Dim cp_name As String
    Dim cp_name_token As String
      
    Dim name As String
   
    Dim start_date As Date
  
    Dim end_date As Date
 
    Dim work_done As Double
    
    Dim total_resources As Double
    
    Dim schedule_row As Range
        
    Dim message As String
    
    Dim tasks As Dictionary
    
    Dim project_name_token
    Dim product_name_token
    
    Dim version_name_token
    
    Dim current_task As ProjectTask
    
    message = ""
    
    check_schedule_ok = True
    
    Set tasks = New Dictionary
    
    For Each schedule_row In schedule_sheet.UsedRange.Rows:
          
        If schedule_row.row > 1 Then
                    
            If (IsError(schedule_row.Cells(1, priority_column).Value)) Then
                 check_schedule_ok = False
                 
                 message = message & "- " & "El campo prioridad de la tarea " & schedule_row.Cells(1, id_column).Value & " es incorrecto (Vacío o menor o igual que 0)" & Chr(13) & Chr(13)
                 
            End If
                                                                        
            Set current_task = obtain_task_from_row(schedule_row)
            
            id = current_task.id
            team_name = current_task.team_name
            group_name = current_task.group_name
            project_name = current_task.project_name
            product_name = current_task.product_name
            version_name = current_task.version
            goal_name = current_task.goal_name
            cp_name = current_task.cp_name
            name = current_task.name
            priority = current_task.priority
            
            If (tasks.exists(id)) Then
                check_schedule_ok = False
                message = message & "- " & "Tarea " & id & " repetida." & Chr(13) & Chr(13)
            
            Else
                tasks.Add id, schedule_row
            End If
                                  
            If (team_name = "") Then
                check_schedule_ok = False
                message = message & "- " & "El campo Team de la tarea " & id & " no es válido." & Chr(13) & Chr(13)
            End If
            
            If (group_name = "") Then
                check_schedule_ok = False
                message = message & "- " & "El campo Group de la tarea " & id & " no es válido." & Chr(13) & Chr(13)
            End If
            
            cp_name_token = ""
            
            If cp_name <> "All" And cp_name <> "" Then
                
                cp_name_token = cp_name & " - "
                
            End If
                        
            version_name_token = ""
            
            If version_name <> "" Then
                
                version_name_token = version_name & " - "
                
            End If
            project_name_token = ""
            
            If project_name <> "" Then
                project_name_token = project_name & " - "
            End If
                
            product_name_token = ""
            
            If product_name <> "" Then
                product_name_token = product_name & " - "
            End If
                                    
            valid_id_name = product_name_token & project_name_token & version_name_token & cp_name_token + name
            
                        
            If (id <> valid_id_name) Then
                
                check_schedule_ok = False
                message = message & "- " & "El campo ID de la tarea " & valid_id_name & " no está bien construido. Tiene que ser autocalculado." & Chr(13) & Chr(13)
                
            End If
            
            If (Not IsError(priority)) Then
                If (priority < 0) Then
                    check_schedule_ok = False
                    message = message & "- " & "El campo prioridad de la tarea " & id & " es incorrecto (menor que 0)" & Chr(13) & Chr(13)
                End If
            End If
        End If
    Next
    
    If Not check_schedule_ok Then
        Err.Raise Number:=1002, _
              Description:=message
    End If
        
End Function

Sub Day_Schedule_Update_From_Resources(current_day As Date)
         
    Dim schedule_row As Range
    
    Dim available_resources As Double
    
    Dim id As String
    Dim remaining As Double
    
    Dim goal_name As String
    
    Dim project_name As String
    
    Dim team_name As String
    Dim group_name As String
    Dim responsible_name As String
    
    Dim version_name As String
      
    Dim cp_name As String
      
    Dim name As String
   
    Dim start_date As Date
  
    Dim end_date As Date
 
    Dim work_done As Double
    
    Dim total_resources As Double
        
    Dim restriction_date_value As Date
    
    Dim current_task As ProjectTask
    Dim task As Variant
    
    Dim same_priority_tasks As Dictionary
    Dim same_priority_tasks_collection As Collection
    
    Dim task_effort As Dictionary
    
    Dim treated_rows As Dictionary
    
    Dim isNotResticted As Boolean
    Dim restricting_task As ProjectTask
    
    Dim dayOfWeek As Integer
    Dim daysToSubtract As Integer
    Dim previousMonday As Date
    Dim new_end_date As Date
            
    total_resources = Round(project_resources.total_resource_number, 2)
    
    If (total_resources >= 0) Then
                                                  
        Schedule.debug_message "Analizando día:" & CStr(current_day)
        
        Set treated_rows = New Dictionary
        
        For Each schedule_row In schedule_sheet.UsedRange.Rows:
                                                                                                                                           
            If schedule_row.row > 1 And Not treated_rows.exists(schedule_row.row) Then
                                                
                Schedule.debug_message "Analizando fila:" & CStr(schedule_row.row)
                
                If (total_resources = 0) Then
                    Exit For
                End If
                                                                                    
                Set current_task = obtain_task_from_row(schedule_row)
                                                                
                remaining = current_task.remaining
                priority = current_task.priority
                                             
                If remaining > 0 And priority > 0 Then
                
                    Schedule.debug_message "Analizando tarea:" & CStr(current_task.id)
                    
                    restriction_date_value = current_task.restriction_date
                    restriction_id = current_task.restriction_id
                    
                    If restriction_id <> "" Then
                        Set restricting_task = tasks(current_task.restriction_id)
                                            
                        isNotResticted = restricting_task.remaining = 0 And current_day > restricting_task.new_end_date
                    Else
                        If IsDate(restriction_date_value) Then
                            isNotResticted = current_day > restriction_date_value
                        Else
                            isNotResticted = True
                        End If
                    End If
                    
                    If (isNotResticted) Then
                                                                                                                                                                                                  
                        Rem All Task with the same priority share resources depending on the remaining.
                            
                        Set same_priority_tasks = Obtain_Same_Priority_Tasks(schedule_row)
                        
                        Set same_priority_tasks_collection = New Collection
                        
                        For Each Item In same_priority_tasks.Keys:
                        
                            treated_rows.Add Item, same_priority_tasks(Item)
                            
                            same_priority_tasks_collection.Add same_priority_tasks(Item)
                            
                        Next
                                                                                                                                                                                
                        next_row = next_row + same_priority_tasks.Count - 1
                                                                                   
                        Set task_effort = Obtain_Same_Priority_Tasks_Effort(same_priority_tasks_collection, current_day, total_resources)
                        
                        For Each task In task_effort.Keys:
                            
                            available_resources = task_effort(task).available_resources
    
                            If available_resources > 0 Then
                            
                                restriction_date_value = task.restriction_date
                                
                                If (current_day > restriction_date_value) Then
                                    goal_name = task.goal_name
                                    project_name = task.project_name
                                    team_name = task.team_name
                                    group_name = task.group_name
                                    responsible_name = task.responsible_name
                                                                                                                                                            
                                    work_done = task.work - task.remaining
                                    
                                    If (IsNull(task.new_start_date) And work_done > 0) Then
                                        start_date = task.old_start_date
                                    Else
                                        start_date = task.new_start_date
                                    
                                    End If
                                                                                                         
                                    project_resources.update_goal_resources True, available_resources, team_name, project_name, group_name, responsible_name, goal_name
                                                            
                                    total_resources = total_resources - available_resources
                                    
                                    If (work_done = 0 Or (start_date > Now() And start_date >= current_day)) Then
                                        
                                        new_start_date = AddBusinessDays(current_day, -4)

                                        task.row.Cells(1, start_date_column) = new_start_date
                                                            
                                        task.new_start_date = new_start_date
                        
                                    Else
                                        task.new_start_date = start_date
                                
                                    End If
                                                                
                                    tasks(task.id).remaining = Round(tasks(task.id).remaining - available_resources, 2)
                                                             
                                    If (tasks(task.id).remaining <= 0) Then
                                        week_days_used = Obtain_Week_Days_Used(tasks(task.id), current_day)
                                        week_days_needed = task_effort(task).week_days_needed
                                        
                                        restriction_date_value = tasks(task.id).restriction_date
                                        available_days = WorksheetFunction.Min(5, BusinessDaysBetween(restriction_date_value, current_day), BusinessDaysBetween(Date, current_day))
                                                                                                                       
                                        new_end_date = AddBusinessDays(WorksheetFunction.Min(AddBusinessDays(current_day, week_days_needed + week_days_used - available_days), current_day), current_task.blocked_days)
                                                                                
                                        Rem new_end_date = AddBusinessDays(current_day, current_task.blocked_days)
                                        
                                        task.row.Cells(1, end_date_column) = new_end_date
                                                                                                                                
                                        task.new_end_date = new_end_date
                                                                                                            
                                    End If
                                                                                                            
                                End If
                                Rem If (current_day > restriction_date_value)
                                
                            End If
                            Rem If available_resources > 0 Then
                                                        
                        Next
                    Else
                    Rem Else of If remaining > 0 And Not current_task.new_end_date Is Nothing Then
                    
                        If remaining = 0 And current_task.new_end_date = 0 And current_task.blocked_days > 0 Then
                            
                            new_end_date = AddBusinessDays(current_day, current_task.blocked_days)
                            
                            Rem new_end_dates(current_task.row.row - 1, 1) = new_end_date
                            current_task.row.Cells(1, end_date_column) = new_end_date
                            current_task.new_end_date = new_end_date
                        End If
                        
                    End If
                    Rem If (current_day > restriction_date_value) Then
                        
                                        
                End If
                Rem If remaining > 0 And Not current_task.new_end_date Is Nothing Then
                
                
                Schedule.debug_message "Tarea Analizada:" & CStr(current_task.id)
                
            End If
            Rem If Not treated_rows.exists(schedule_row.row) Then
            
        Next
    
    End If

End Sub

Function obtain_task_from_row(schedule_row As Range) As ProjectTask

    Dim id As String
    
    Dim remaining As Double
    Dim blocked_days As Double
    Dim work As Double
    
    Dim team_name As String
    Dim group_name As String
    Dim responsible_name As String
    Dim project_name As String
    Dim version_name As String
    Dim cp_name As String
    Dim name As String
    
    Dim resources As Double
    
    Dim priority As Object
    
    Dim start_date As Date
    Dim end_date As Date
    Dim restriction_date As Date
    
    Dim restriction As RestrictionType
    
    id = schedule_row.Cells(1, id_column).Value
    
    If Not tasks.exists(id) Then
        Set obtain_task_from_row = New ProjectTask
        
        Set obtain_task_from_row.row = schedule_row
        
        team_name = schedule_row.Cells(1, team_column).Value
        group_name = schedule_row.Cells(1, group_column).Value
        responsible_name = schedule_row.Cells(1, responsible_column).Value
        project_name = schedule_row.Cells(1, project_column).Value
        product_name = schedule_row.Cells(1, product_column).Value
        goal_name = schedule_row.Cells(1, goal_column).Value
        version_name = schedule_row.Cells(1, version_column).Value
        cp_name = schedule_row.Cells(1, cp_column).Value
        name = schedule_row.Cells(1, name_column).Value
        
        start_date = schedule_row.Cells(1, start_date_column)
        end_date = schedule_row.Cells(1, end_date_column)
        
        Set restriction = obtain_restriction_date_from_row(schedule_row)
        
        If (restriction.restriction_task = "") Then
            restriction_date = obtain_restriction_date_from_row(schedule_row).restriction_date
            restriction_id = ""
        Else
            restriction_id = obtain_restriction_date_from_row(schedule_row).restriction_task
            Rem restriction_date = Null
            
        End If
                                                          
        resources_max = schedule_row.Cells(1, resource_max_column).Value
        
        Set remaining_value = schedule_row.Cells(1, remaining_column)
        
        If remaining_value = "N/A" Then
            remaining = 0
        Else
            remaining = schedule_row.Cells(1, remaining_column).Value / 5
        End If
        
        If blocked_days_column = 0 Then
            blocked_days = 0
            
        Else
            blocked_days = schedule_row.Cells(1, blocked_days_column).Value
            
        End If
        
        work = schedule_row.Cells(1, work_column).Value / 5
        
        
        Set priority = schedule_row.Cells(1, priority_column)
        
        obtain_task_from_row.team_name = team_name
        obtain_task_from_row.group_name = group_name
        obtain_task_from_row.responsible_name = responsible_name
        obtain_task_from_row.project_name = project_name
        obtain_task_from_row.product_name = product_name
        obtain_task_from_row.version = version_name
        obtain_task_from_row.goal_name = goal_name
        obtain_task_from_row.cp_name = cp_name
        obtain_task_from_row.name = name
        obtain_task_from_row.id = id
        
        obtain_task_from_row.old_start_date = start_date
        obtain_task_from_row.old_end_date = end_date
        
        If remaining = 0 And blocked_days = 0 Then
            obtain_task_from_row.new_end_date = end_date
        Else
            obtain_task_from_row.new_end_date = 0
        End If
        
        obtain_task_from_row.restriction_date = restriction_date
        obtain_task_from_row.restriction_id = restriction_id
        
        obtain_task_from_row.resources_max = resources_max
        
        If (priority = "") Then
            obtain_task_from_row.priority = 0
        Else
            obtain_task_from_row.priority = priority
        End If
                
        obtain_task_from_row.remaining = remaining
        obtain_task_from_row.work = work
        obtain_task_from_row.blocked_days = blocked_days
        
        tasks.Add id, obtain_task_from_row
                                  
    Else
            
        Set obtain_task_from_row = tasks(id)
                                  
    End If
    
End Function

Function Obtain_Same_Priority_Tasks(schedule_row As Range) As Dictionary

    Dim current_row_priority As Double
    Dim next_priority As Double
    Dim current_responsible As String
    Dim next_responsible As String
    
    Dim remaining As Double
    
    Dim current_row As Range
        
    Dim id_column As Integer
    Dim id As String
    
    Dim current_task As ProjectTask
           
    Set Obtain_Same_Priority_Tasks = New Dictionary
        
    Set current_task = obtain_task_from_row(schedule_row)
     
    current_row_priority = current_task.priority
    next_priority = current_row_priority
    
    current_responsible = current_task.team_name & "##" & current_task.group_name & "##" & current_task.responsible_name
    next_responsible = current_responsible
    
    Set current_row = schedule_row
        
    Do Until next_priority <> current_row_priority
                
        If next_responsible = current_responsible And current_task.remaining > 0 Then
            Obtain_Same_Priority_Tasks.Add current_task.row.row, current_task
        End If
                  
        Set current_task = obtain_task_from_row(schedule_sheet.UsedRange.Rows(current_task.row.row + 1))
        
        next_priority = current_task.priority
        next_responsible = current_task.team_name & "##" & current_task.group_name & "##" & current_task.responsible_name
    
    Loop
    
End Function

Function Obtain_Same_Priority_Tasks_Effort(same_prio_tasks As Collection, current_day As Date, total_resources As Double) As Dictionary

    Dim current_row_priority As Double
    Dim next_priority As Double
    Dim remaining As Double
    
    Dim task As ProjectTask
    
    Dim task_weights As Dictionary
    Dim task_resources As Dictionary
        
    Set task_weights = Obtain_Task_Weight(same_prio_tasks, current_day)
                       
    Set Obtain_Same_Priority_Tasks_Effort = Obtain_Task_Resources_By_Weigth(same_prio_tasks, task_weights, current_day, total_resources)
               
End Function

Function Obtain_Task_Resources_By_Weigth(tasks As Collection, task_weights As Dictionary, current_day As Date, total_resources As Double) As Dictionary
    Dim current_resources As Double
    Dim available_resources As Double
    
    Dim task_resources_auxiliar As Dictionary
    
    Dim task_weight_candidates As Collection
    Dim recalculate As Boolean
    
    Dim task As ProjectTask
    
    Set Obtain_Task_Resources_By_Weigth = New Dictionary
   
    Set task_weight_candidates = New Collection
    
    current_resources = 0
    
    recalculate = False
                   
    For Each task In tasks:
                    
        Set week_available_resources = Obtain_Available_Resources(task, current_day, task_weights(task))
        available_resources = week_available_resources.available_resources
                                                        
        If (total_resources * task_weights(task) > available_resources) Then
                                
            Obtain_Task_Resources_By_Weigth.Add task, week_available_resources
            
            recalculate = True
        Else
            If (task_weights(task) > 0) Then
                task_weight_candidates.Add task
            End If
        End If
            
    Next
    
    If (recalculate And task_weight_candidates.Count > 0) Then
    
        Set task_resources_auxiliar = Obtain_Task_Resources_By_Weigth(task_weight_candidates, Obtain_Task_Weight(task_weight_candidates, current_day), current_day, total_resources)
        
        For Each task In task_weight_candidates:
        
            Obtain_Task_Resources_By_Weigth.Add task, task_resources_auxiliar(task)
        Next
                                      
    End If
    
    If (Not recalculate And task_weight_candidates.Count > 0) Then
        For Each task In task_weight_candidates:
            
            Set week_available_resources = New WeekAvaliableResources
            
            week_available_resources.available_resources = total_resources * task_weights(task)
            week_available_resources.week_days_needed = 5
            
            Obtain_Task_Resources_By_Weigth.Add task, week_available_resources
            
        Next
    End If

End Function
 

Function Obtain_Task_Weight(same_prio_tasks As Collection, current_day As Date) As Dictionary
    
    Dim task As ProjectTask
    Dim group_name
    Dim total_remaining As Dictionary
    
    Set total_remaining = New Dictionary
       
    Set Obtain_Task_Weight = New Dictionary
        
    Dim restriction_date_value As Date
    
    
    For Each task In same_prio_tasks:
        
        group_name = task.group_name
        restriction_date_value = task.restriction_date
        
        If restriction_date_value <= current_day Then
            If (total_remaining.exists(group_name)) Then
        
                total_remaining(group_name) = total_remaining(group_name) + task.remaining
            Else
                total_remaining(group_name) = task.remaining
            
            End If
        End If
    Next
    
    For Each task In same_prio_tasks:
    
        restriction_date_value = task.restriction_date
        group_name = task.group_name
        
        If (task.remaining = 0) Or (restriction_date_value > current_day) Or total_remaining(group_name) = 0 Then
            Obtain_Task_Weight.Add task, 0
        Else
            
            Obtain_Task_Weight.Add task, (task.remaining / total_remaining(group_name))
        End If
    Next
End Function

Function Obtain_Used_Resources_By_Same_Team(task As ProjectTask, current_day As Date) As Double
    
    Dim team_name As String
    Dim group_name As String
    Dim responsible_name As String
    Dim project_name As String
    Dim goal_name As String
    
    team_name = task.team_name
    group_name = task.group_name
    responsible_name = task.responsible_name
    project_name = task.project_name
    
    Obtain_Used_Resources_By_Same_Team = project_resources.obtain_used_goal_resources(team_name, "TOTAL", group_name, responsible_name)
    
End Function

Function Obtain_Available_Resources_By_Same_Team(task As ProjectTask, current_day As Date) As Double
    
    Dim team_name As String
    Dim group_name As String
    Dim responsible_name As String
    Dim project_name As String
    Dim goal_name As String
    
    team_name = task.team_name
    group_name = task.group_name
    responsible_name = task.responsible_name
    project_name = task.project_name
    
    Obtain_Available_Resources_By_Same_Team = project_resources.obtain_available_goal_resources(team_name, "TOTAL", group_name, responsible_name)
    
End Function

Function Obtain_Week_Days_Used(task As ProjectTask, current_day As Date) As Double
    
    Dim available_resources As Double
    
    available_resources = Obtain_Available_Resources_By_Same_Team(task, current_day)
    
    If available_resources > 0.01 Then
    
        Obtain_Week_Days_Used = Round(5 * Obtain_Used_Resources_By_Same_Team(task, current_day) / available_resources)
    
    Else
        Obtain_Week_Days_Used = 0
    End If
    
End Function



Function Obtain_Available_Resources(task As ProjectTask, current_day As Date, weight As Double) As WeekAvaliableResources
       
    Dim team_name As String
    Dim group_name As String
    Dim responsible_name As String
    Dim project_name As String
    Dim goal_name As String
    
    Dim goal_key As String
    Dim project_key As String
    
    Dim goal_resource_number As Double
    Dim project_resource_number As Double
    Dim task_resource_number As Double
    
    Dim remaining As Double
    
    Dim week_ratio As Double
    
    Set Obtain_Available_Resources = New WeekAvaliableResources
    
    team_name = task.team_name
    group_name = task.group_name
    responsible_name = task.responsible_name
    project_name = task.project_name
    goal_name = task.goal_name
    
    remaining = task.remaining
    
    week_ratio = WorksheetFunction.Min(5, current_day - restriction_date_value) / 5
    
    goal_resource_number = project_resources.obtain_goal_resources(team_name, project_name, group_name, responsible_name, goal_name) * week_ratio * weight
    
    task_resource_number = task.resources_max * week_ratio
    
    If (task_resource_number = 0) Then
        available_resources = goal_resource_number
    Else
        available_resources = WorksheetFunction.Min(goal_resource_number, task_resource_number)
    End If
        
    Obtain_Available_Resources.available_resources = WorksheetFunction.Min(available_resources, remaining)
       
    If (available_resources > 0.01) Then
        Obtain_Available_Resources.week_days_needed = WorksheetFunction.Min(Int(5 * remaining / available_resources) + 1, 5)
    Else
        Obtain_Available_Resources.week_days_needed = 5
    End If

End Function


Function obtain_restriction_date_from_row(ByRef currentRow As Range) As RestrictionType
    
    Dim restriction_date_value
    Dim current_date_value As Date
    
    Set obtain_restriction_date_from_row = New RestrictionType
    
    restriction_date_value = currentRow.Cells(1, restriction_date_column)
    
    If Not date_sheet Is Nothing Then
            current_date_value = date_sheet.Cells(3, 2).Value
        Else
            current_date_value = Date
        End If
        
    If IsDate(restriction_date_value) Or restriction_date_value = "" Then
        
        obtain_restriction_date_from_row.restriction_task = ""
        
        If restriction_date_value = "" Or restriction_date_value < current_date_value Then
            
          obtain_restriction_date_from_row.restriction_date = current_date_value
        
        Else
            
          obtain_restriction_date_from_row.restriction_date = restriction_date_value
            
        End If
    Else
        Rem Restriction given by other task (by Id)
        
        obtain_restriction_date_from_row.restriction_task = restriction_date_value
        obtain_restriction_date_from_row.restriction_date = current_date_value
        
    End If
           
End Function

Sub analyze_date_changes()

    Dim current_task As ProjectTask
    
    Dim last_changes_sheet As Worksheet
    Dim last_row As Integer
            
    Set last_changes_sheet = Sheets("Last Changes")
    last_row = last_changes_sheet.UsedRange.Rows.Count
     
    For Each key In tasks.Keys
        
        If Not IsEmpty(key) Then
        
            Set current_task = tasks(key)
        
            analyze_date_change current_task
            
        End If
        
    Next
    
    If (last_row <> 1) Then
        last_changes_sheet.Range("A2:I" & last_row).Delete
    End If
    

End Sub

Sub analyze_date_change(ByRef current_task As ProjectTask)
    
    Dim last_changes_sheet As Worksheet
    Dim last_row As Integer
    
    If (current_task.old_start_date <> current_task.new_start_date Or current_task.old_end_date <> current_task.new_end_date) Then
                
        Set last_changes_sheet = Sheets("Last Changes")
        last_row = last_changes_sheet.UsedRange.Rows.Count + 1
        
        With last_changes_sheet
        
            .Cells(last_row, 1) = current_task.project_name
            .Cells(last_row, 2) = current_task.version
            .Cells(last_row, 3) = current_task.goal_name
            .Cells(last_row, 4) = current_task.cp_name
            .Cells(last_row, 5) = current_task.name
            .Cells(last_row, 6) = current_task.old_start_date
            .Cells(last_row, 7) = current_task.new_start_date
            .Cells(last_row, 8) = current_task.old_end_date
            .Cells(last_row, 9) = current_task.new_end_date
            
        End With
        
    End If
    
End Sub
Function BusinessDaysBetween(startDate As Date, endDate As Date) As Long
    Dim currentDate As Date
    Dim businessDaysCount As Long
    Dim dayStep As Integer
    
    currentDate = startDate
    businessDaysCount = 0
    
    ' Determina la dirección del conteo basado en la comparación de las fechas
    If endDate >= startDate Then
        dayStep = 1 ' Mover hacia adelante
    Else
        dayStep = -1 ' Mover hacia atrás
    End If
    
    ' Loop through the days between startDate and endDate
    Do While (dayStep > 0 And currentDate <= endDate) Or (dayStep < 0 And currentDate >= endDate)
        ' Check if the current date is a business day (not a weekend and not a holiday)
        If Not (Weekday(currentDate) = vbSunday Or Weekday(currentDate) = vbSaturday) Then
            If Not IsHoliday(currentDate) Then
                ' Increment or decrement the business days count based on direction
                businessDaysCount = businessDaysCount + dayStep
            End If
        End If
        ' Move to the next or previous day based on direction
        currentDate = currentDate + dayStep
    Loop
    
    ' Adjust the count for the reverse direction
    If dayStep < 0 Then
        ' If counting backwards, subtract one to account for the start date not being included
        businessDaysCount = businessDaysCount - 1
    End If
    
    BusinessDaysBetween = businessDaysCount
End Function


Function AddBusinessDays(startDate As Date, numDays As Long) As Date
  Dim currentDate As Date
  currentDate = startDate

  ' Loop until we have added or subtracted the desired number of business days
  Do While numDays <> 0
    ' Determine direction based on whether numDays is positive or negative
    If numDays > 0 Then
       currentDate = currentDate + 1  ' Move forward
    Else
       currentDate = currentDate - 1 ' Move backward
    End If

    ' Check if the current date is a business day (not a weekend and not a holiday)
    If Not (Weekday(currentDate) = vbSunday Or Weekday(currentDate) = vbSaturday) Then
       If Not IsHoliday(currentDate) Then
          ' Adjust numDays closer to zero
          If numDays > 0 Then
             numDays = numDays - 1
          Else
             numDays = numDays + 1
          End If
       End If
    End If
  Loop

  AddBusinessDays = currentDate
End Function

Function IsHoliday(checkDate As Date) As Boolean

' List of fixed holidays in Madrid, Spain
  Dim fixedHolidays As Variant
  fixedHolidays = Array(#1/1/2022#, #1/6/2022#, #5/1/2022#, #8/15/2022#, #10/12/2022#, #11/1/2022#, #12/6/2022#, #12/8/2022#, #12/25/2022#)

  ' Check if the checkDate is in the list of fixed holidays
  If (UBound(Filter(fixedHolidays, checkDate)) > -1) Then
    IsHoliday = True
    Exit Function
  End If

  ' Check if the checkDate is between December 24 and December 31
  If (checkDate >= DateSerial(Year(checkDate), 12, 24)) And (checkDate <= DateSerial(Year(checkDate), 12, 31)) Then
    IsHoliday = True
    Exit Function
  End If
  
  ' Check if the checkDate is on Easter
  If checkDate >= (EasterSunday(Year(checkDate)) - 7) And checkDate <= EasterSunday(Year(checkDate)) Then
  
    IsHoliday = True
    Exit Function
  End If
  
End Function




Function EasterSunday(currentYear As Integer) As Date
    If easter_sundays.exists(currentYear) Then
        EasterSunday = easter_sundays(currentYear)
    Else
        Dim a As Integer, b As Integer, c As Integer, d As Integer, e As Integer
        Dim f As Integer, g As Integer, h As Integer, i As Integer, j As Integer
        Dim k As Integer, l As Integer, m As Integer, n As Integer, p As Integer
        
        a = currentYear Mod 19
        b = currentYear \ 100
        c = currentYear Mod 100
        d = b \ 4
        e = b Mod 4
        f = (b + 8) \ 25
        g = (b - f + 1) \ 3
        h = (19 * a + b - d - g + 15) Mod 30
        i = c \ 4
        k = c Mod 4
        l = (32 + 2 * e + 2 * i - h - k) Mod 7
        m = (a + 11 * h + 22 * l) \ 451
        n = (h + l - 7 * m + 114) \ 31
        p = (h + l - 7 * m + 114) Mod 31 + 1
        EasterSunday = DateSerial(currentYear, n, p)
        easter_sundays.Add currentYear, EasterSunday
        
    End If
End Function
