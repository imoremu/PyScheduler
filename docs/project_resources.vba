Private available_resources_goals As Dictionary
Private used_resources_goals As Dictionary

Private available_resources_sheet As Worksheet
Private used_resources_sheet As Worksheet

Private current_available_resource_column As Integer
Private current_used_resource_column As Integer

Private available_resources_table As ListObject
Private used_resources_table As ListObject

Private Const TOTAL_TAG = "TOTAL"
Private Const ALL_TAG = "*"

Private used_resources_matrix() As Variant
Private used_resources_matrix_tx() As Variant

Private available_resources_matrix() As Variant

Private columna_inicial_recursos As Double


Public Sub init(available_resources_sheet_in As Worksheet, used_resources_sheet_in As Worksheet)
  
    Set available_resources_sheet = available_resources_sheet_in
    Set used_resources_sheet = used_resources_sheet_in
    
    Set used_resources_table = used_resources_sheet.ListObjects("T_Used_Resources")
    Set available_resources_table = available_resources_sheet.ListObjects("T_Available_Resources")
        
    columna_inicial_recursos = 1
    
    For Each headerRange In used_resources_table.HeaderRowRange
        If IsDate(headerRange.Value) Then
            Exit For
        End If
        
        columna_inicial_recursos = columna_inicial_recursos + 1
        
    Next headerRange
        
    If columna_inicial_recursos > used_resources_table.ListColumns.Count Then
        MsgBox "No se encontraron columnas con fechas válidas en la tabla."
    End If
    
    If used_resources_table.AutoFilter.FilterMode = True Then
        used_resources_table.AutoFilter.ShowAllData
    End If
    
    If available_resources_table.AutoFilter.FilterMode = True Then
        available_resources_table.AutoFilter.ShowAllData
    End If
    
    init_available_resources_goals
    init_used_resources_goals
    
    current_available_resource_column = 3
    current_used_resource_column = 3
    
End Sub

Property Get goals() As Dictionary
     Set goals = dgoals
End Property

REM MIGRACIÓN: Update_day no aplica en python pandas (podemos usar el nombre de columna)
Public Sub update_day(available_resource_column As Integer, current_day As Date)
            
    current_available_resource_column = available_resource_column
                   
    For Each date_column In used_resources_sheet.Rows(1).Columns()
        
        If (date_column.Column >= current_used_resource_column) And (IsDate(date_column.Cells(1, 1).Value)) Then
        
            If (date_column.Cells(1, 1) >= current_day) Then
                        
                current_used_resource_column = date_column.Column
                Exit For
                
            End If
        End If
    Next
    
End Sub

REM MIGRACIÓN: init_available_resources_goals available_resource_matrix no aplica en python pandas (podemos usar el nombre de columna)
Private Sub init_available_resources_goals()
    
    Dim goal_project_pair As Collection
    
    Dim team_column As Integer
    Dim project_column As Integer
    Dim group_column As Integer
    Dim resource_column As Integer
    Dim goal_column As Integer
    
    Dim team_name As String
    Dim project_name As String
    Dim group_name As String
    Dim resource_name As String
    Dim goal_name As String
    
    Dim goal_row As ListRow
    
    Set available_resources_goals = New Dictionary
    
    Application.StatusBar = "Initialization - Used Resources"
        
    team_column = available_resources_table.ListColumns("Team").Index
    project_column = available_resources_table.ListColumns("Project").Index
    group_column = available_resources_table.ListColumns("Group").Index
    resource_column = available_resources_table.ListColumns("Responsible").Index
    goal_column = available_resources_table.ListColumns("Goal").Index
    
    For Each goal_row In available_resources_table.ListRows
                
        team_name = goal_row.Range.Cells(1, team_column).Value
        project_name = goal_row.Range.Cells(1, project_column).Value
        group_name = goal_row.Range.Cells(1, group_column).Value
        resource_name = goal_row.Range.Cells(1, resource_column).Value
        goal_name = goal_row.Range.Cells(1, goal_column).Value
                                  
        available_resources_goals.Add key(team_name, project_name, group_name, resource_name, goal_name), goal_row.Index
                
    Next
    
    available_resources_matrix = available_resources_table.DataBodyRange.Value

End Sub

REM MIGRACIÓN: init_used_resources_goals no aplica en python pandas (podemos usar el nombre de columna)
Private Sub init_used_resources_goals()

    Dim goal_project_pair As Collection
    
    Dim team_name As String
    Dim project_name As String
    Dim group_name As String
    Dim resource_name As String
    Dim goal_name As String
    Dim priority_name As String
    
    Dim goal_row As ListRow
    
    Dim userResourcesRange As Range
    Dim rowCount As Long
    Dim columnCount As Long

    
    
    Set used_resources_goals = New Dictionary
    
    Application.StatusBar = "Initialization - Used Resources"
    
    With used_resources_table
    
        team_column = .ListColumns("Resource Team").Index
        project_column = .ListColumns("Resource Project").Index
        group_column = .ListColumns("Resource Group").Index
        resource_column = .ListColumns("Resource Responsible").Index
        goal_column = .ListColumns("Resource Goal").Index
        
        used_resources_matrix = .DataBodyRange.Formula
        used_resources_matrix_tx = transpose_matrix(used_resources_matrix)
        
    End With
    
    For Each goal_row In used_resources_table.ListRows
        With goal_row.Range
            
            team_name = .Cells(1, team_column).Value
            project_name = .Cells(1, project_column).Value
            group_name = .Cells(1, group_column).Value
            resource_name = .Cells(1, resource_column).Value
            goal_name = .Cells(1, goal_column).Value
                                  
        End With
        
        used_resources_goals.Add key(team_name, project_name, group_name, resource_name, goal_name), goal_row.Index
        
    Next
            
                    
End Sub

Public Sub update_goal_resources(increase As Boolean, resources_used As Double, team As String, Optional project As String = TOTAL_TAG, Optional group As String = TOTAL_TAG, Optional resource As String = TOTAL_TAG, Optional goal As String = ALL_TAG)

    Dim current_key As String
    Dim resources_row As Integer
  
    Dim day_cell As Range
        
    Dim current_resources
    
    Dim rows_number As Integer
    
    Dim new_row As ListRow
    
    Dim update As Boolean
            
    update = True
    
    Rem This control is done to avoid having one entrance per project in used resources if all the projects are managed by the same team.
    
    If Not available_resources_goals.exists(key(team, project, group, resource)) And goal = "*" Then
        If available_resources_goals.exists(key(team, TOTAL_TAG, group, resource)) Then
            project = TOTAL_TAG
        Else
            update = False
        End If
     End If
                   
    If update Then
    
        resources_row = obtain_used_resources_goal_row(team, project, group, resource, goal)
        
        If (increase) Then
            Rem -- CR--
            Rem current_resources = used_resources_sheet.ListObjects(1).dataBodyRange.Cells(resources_row, current_used_resource_column).Value
            current_resources = used_resources_matrix_tx(current_used_resource_column, resources_row)
            current_resources = current_resources + resources_used
        
        Else
            current_resources = resources_used
        
        End If
        
        Rem -- CR--
        Rem used_resources_sheet.ListObjects(1).dataBodyRange.Cells(resources_row, current_used_resource_column).Value = current_resources
        used_resources_matrix_tx(current_used_resource_column, resources_row) = current_resources
        
        
    End If
    
    If goal <> ALL_TAG Then
        
        update_goal_resources True, resources_used, team, project, group, resource
    
    ElseIf resource <> TOTAL_TAG Then
            
        update_goal_resources True, resources_used, team, project, group
            
    ElseIf group <> TOTAL_TAG Then
            
        update_goal_resources True, resources_used, team, project
                
    ElseIf project <> TOTAL_TAG Then
            
        update_goal_resources True, resources_used, team
                    
    End If
    
End Sub

Public Function obtain_goal_resources(team_name As String, Optional project_name As String = TOTAL_TAG, Optional group_name As String = TOTAL_TAG, Optional resource_name As String = TOTAL_TAG, Optional goal_name As String = ALL_TAG) As Double

    Dim available_goal_resources As Double
    Dim used_goal_resources As Double
       
    Dim available_project_resources As Double
    Dim used_project_resources As Double
    
    Dim resource_resources As Double
    Dim goal_resources As Double
    Dim group_resources As Double
    Dim project_resources As Double
               
    If (project_name = TOTAL_TAG And Not available_resources_goals.exists(key(team_name))) Then
        Err.Raise Number:=1001, _
              Description:="Available Resources must fill Project TOTAL / Group TOTAL / Responsible TOTAL / Goal * for each Team" & vbNewLine
        
    End If
    
    If available_resources_goals.exists(key(team_name, project_name)) Then
        project_resources = total_goal_resources(team_name, project_name)
        
    ElseIf available_resources_goals.exists(key(team_name, TOTAL_TAG)) Then
        project_resources = total_goal_resources(team_name, TOTAL_TAG)
        
    Else
        project_resources = obtain_goal_resources(team_name)
    End If
                
    If available_resources_goals.exists(key(team_name, project_name, group_name)) Then
        group_resources = total_goal_resources(team_name, project_name, group_name)
    Else
        group_resources = project_resources
        
        If available_resources_goals.exists(key(team_name, TOTAL_TAG, group_name)) Then
            general_group_resources = total_goal_resources(team_name, TOTAL_TAG, group_name)
            
            group_resources = WorksheetFunction.Min(group_resources, general_group_resources)
        End If
        
    End If
            
    If available_resources_goals.exists(key(team_name, project_name, group_name, resource_name)) Then
        resource_resources = total_goal_resources(team_name, project_name, group_name, resource_name)
    Else
    
        resource_resources = group_resources
        
        If available_resources_goals.exists(key(team_name, TOTAL_TAG, TOTAL_TAG, resource_name)) Then
            general_resource_resources = total_goal_resources(team_name, TOTAL_TAG, TOTAL_TAG, resource_name)
            
            resource_resources = WorksheetFunction.Min(resource_resources, general_resource_resources)
        End If
    End If
    
    If available_resources_goals.exists(key(team_name, project_name, group_name, resource_name, goal_name)) Then
        goal_resources = total_goal_resources(team_name, project_name, group_name, resource_name, goal_name)
    Else
        goal_resources = resource_resources
    End If
            
    obtain_goal_resources = WorksheetFunction.Min(project_resources, group_resources, resource_resources, goal_resources)
        
End Function
Public Function total_goal_resources(team_name As String, Optional project_name As String = TOTAL_TAG, Optional group_name As String = TOTAL_TAG, Optional resource As String = TOTAL_TAG, Optional goal_name As String = ALL_TAG) As Double
    
    Dim available_goal_resources As Double
    Dim used_goal_resources As Double
    
    Rem -- CR --
    Rem available_goal_resources = available_resources_sheet.ListObjects(1).dataBodyRange.Cells(available_resources_goals(key(team_name, project_name, group_name, resource, goal_name)), current_available_resource_column).Value
    available_goal_resources = obtain_available_goal_resources(team_name, project_name, group_name, resource, goal_name)
    
    Rem -- CR --
    Rem used_goal_resources = used_resources_sheet.ListObjects(1).dataBodyRange.Cells(obtain_used_resources_goal_row(team_name, project_name, group_name, resource, goal_name), current_used_resource_column).Value
    used_goal_resources = obtain_used_goal_resources(team_name, project_name, group_name, resource, goal_name)
    
    total_goal_resources = available_goal_resources - used_goal_resources
    
End Function

Public Function obtain_available_goal_resources(team_name As String, Optional project_name As String = TOTAL_TAG, Optional group_name As String = TOTAL_TAG, Optional resource As String = TOTAL_TAG, Optional goal_name As String = ALL_TAG) As Double
                
    Dim available_resources As Double
    
    available_resources = available_resources_goals(key(team_name, project_name, group_name, resource, goal_name))
    
    If available_resources = 0 Then
        obtain_available_goal_resources = 0
    Else
        obtain_available_goal_resources = available_resources_matrix(available_resources_goals(key(team_name, project_name, group_name, resource, goal_name)), current_available_resource_column)
    End If

End Function

Public Function total_resource_number() As Double
    
    Dim available_resources As Double
    Dim used_resources As Double
        
    total_resource_number = available_resources_sheet.ListObjects(1).TotalsRowRange.Cells(1, current_available_resource_column).Value
    
End Function

Public Function obtain_used_goal_resources(team_name As String, Optional project_name As String = TOTAL_TAG, Optional group_name As String = TOTAL_TAG, Optional resource As String = TOTAL_TAG, Optional goal_name As String = ALL_TAG) As Double
                
    obtain_used_goal_resources = used_resources_matrix_tx(current_used_resource_column, obtain_used_resources_goal_row(team_name, project_name, group_name, resource, goal_name))

End Function

Private Function obtain_used_resources_goal_row(team_name As String, Optional project_name As String = TOTAL_TAG, Optional group_name As String = TOTAL_TAG, Optional resource_name As String = TOTAL_TAG, Optional goal_name As String = ALL_TAG) As Double
        
    Dim numRows As Long
    Dim numCols As Long
        
    If Not used_resources_goals.exists(key(team_name, project_name, group_name, resource_name, goal_name)) Then
    
        new_num_columns = UBound(used_resources_matrix_tx, 2) + 1
        num_rows = UBound(used_resources_matrix_tx, 1)
                        
        Rem -- CR --
        Rem Set new_row = used_resources_sheet.ListObjects(1).ListRows.Add
                                                
        ReDim Preserve used_resources_matrix_tx(1 To num_rows, 1 To new_num_columns)
        
        used_resources_matrix_tx(1, new_num_columns) = team_name
        used_resources_matrix_tx(2, new_num_columns) = project_name
        used_resources_matrix_tx(3, new_num_columns) = group_name
        used_resources_matrix_tx(4, new_num_columns) = resource_name
        used_resources_matrix_tx(5, new_num_columns) = goal_name
        
        For current_column = 6 To columna_inicial_recursos
            used_resources_matrix_tx(current_column, new_num_columns) = "=IF([@[Resource Goal]]=""*"","""",IFERROR(INDEX(T_Schedule[" & used_resources_table.ListColumns(current_column).name & "],MATCH([@[Resource Goal]],T_Schedule[Goal],0),1),""""))"
            ''used_resources_matrix_tx(current_column, new_num_columns) = ""
        Next current_column
        
        used_resources_goals.Add key(team_name, project_name, group_name, resource_name, goal_name), new_num_columns
            
        Rem -- CR --
        Rem .Range(Cells(1, 7), Cells(1, .Columns.Count)).Value = 0
        For c = columna_inicial_recursos To num_rows
            used_resources_matrix_tx(c, new_num_columns) = 0
        Next c
        
        Rem -- CR --
        Rem End With
        
    End If
    
    obtain_used_resources_goal_row = used_resources_goals(key(team_name, project_name, group_name, resource_name, goal_name))

End Function

Public Sub update_sheet()

    Dim num_rows As Long
    Dim num_cols As Long
    
    Schedule.debug_message "Updating sheet..."
    
    used_resources_matrix = transpose_matrix(used_resources_matrix_tx)
    
    num_rows = UBound(used_resources_matrix, 1) + 1
    num_cols = UBound(used_resources_matrix, 2)
    
    used_resources_table.Resize used_resources_table.Range.Resize(num_rows, num_cols)
    used_resources_table.DataBodyRange.Formula = used_resources_matrix
    
    Schedule.debug_message "Sheet updated"
    
End Sub


Private Function exists(key As String) As Boolean
    exists = available_resources_goals.exists(key)
End Function

Private Function key(team As String, Optional project As String = TOTAL_TAG, Optional group As String = TOTAL_TAG, Optional resource As String = TOTAL_TAG, Optional goal As String = ALL_TAG) As String
                  
    If project = TOTAL_TAG And group = TOTAL_TAG And resource = TOTAL_TAG And goal = ALL_TAG Then
        key = Trim(team)
                  
    ElseIf group = TOTAL_TAG And resource = TOTAL_TAG And goal = ALL_TAG Then
        key = Trim(team) & "##" & Trim(project)
        
    ElseIf resource = TOTAL_TAG And goal = ALL_TAG Then
        key = Trim(team) & "##" & Trim(project) & "##" & Trim(group)
    
    ElseIf goal = ALL_TAG Then
    
        key = Trim(team) & "##" & Trim(project) & "##" & Trim(group) & "##" & Trim(resource)
    Else
    
        key = Trim(team) & "##" & Trim(project) & "##" & Trim(group) & "##" & Trim(resource) & "##" & Trim(goal)
    
    End If
    
End Function


Sub Clean_Used_Resources(clean_date As Date)

    Dim resource_sheet As Worksheet
    Dim used_res_table As ListObject
    Dim resource_column As ListColumn
    Dim resource_row As Range
    
    Dim rowStart As Long
    Dim rowEnd As Long
    Dim colStart As Long
    Dim colEnd As Long
    
    Set resource_sheet = Sheets("Used Resources")
    
    Application.StatusBar = "Initialization - Clean Used Resources"
    
    
    rowStart = 1
    rowEnd = UBound(used_resources_matrix_tx, 2)
    colEnd = UBound(used_resources_matrix_tx, 1)
    
    Rem -- CR --
    If (used_resources_table.ListRows.Count > 0) Then
        For Each resource_column In used_resources_table.ListColumns
            If IsDate(resource_column.name) Then
                If CDate(resource_column.name) > clean_date Then
                    Rem -- CR --
                    Rem used_resources_sheet.Activate
                    Rem used_resources_table.dataBodyRange.Range(Cells(1, resource_column.Index), Cells(used_res_table.ListRows.Count, used_res_table.ListColumns.Count)).Value = 0
                    
                    Dim r As Long
                    For r = rowStart To rowEnd
                        Dim c As Long
                        For c = resource_column.Index To colEnd
                            used_resources_matrix_tx(c, r) = 0
                        Next c
                    Next r
                    
                    Exit For
                End If
            End If
        Next
    End If
    
    Rem -- CR --
    Rem used_resources_sheet.Calculate
    
End Sub


Private Function transpose_matrix(matrix() As Variant) As Variant()

    ' Transposing the matrix
    Dim transposed_matrix() As Variant
    Dim matrix_columns As Long, matrix_rows As Long
    
    matrix_columns = UBound(matrix, 2)
    matrix_rows = UBound(matrix, 1)
    
    ReDim transposed_matrix(1 To matrix_columns, 1 To matrix_rows)
    
    Dim i As Long, j As Long
    For i = 1 To matrix_columns
        For j = 1 To matrix_rows
            transposed_matrix(i, j) = matrix(j, i)
        Next j
    Next i
    
    transpose_matrix = transposed_matrix
    
End Function
