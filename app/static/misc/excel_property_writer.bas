Attribute VB_Name = "excel_property_writer"
Option Explicit

Public Const SW_DM_KEY As String = "ActiveWeighingSolution:swdocmgr_general-11785-02051-00064-17409-08598-34307-00007-48552-23216-29074-08612-43094-04219-29835-61445-08235-16213-33488-54400-16572-25610-24574-36100-42449-38361-38237-40357-42401-40377-48461-54705-42449-47549-14337-26722-58970-57546-25690-25696-986"

'Const SW_DM_KEY As String = "ActiveWeighingSolution: swdocmgr_general -11785 - 2051 - 64 - 17409 - 8598 - 34307 - 7 - 48552 - 23216 - 29074 - 8612 - 43094 - 4219 - 29835 - 61445 - 8235 - 16213 - 33488 - 54400 - 16572 - 25610 - 24574 - 36100 - 42449 - 38361 - 38237 - 40357 - 42401 - 40377 - 48461 - 54705 - 42449 - 47549 - 14337 - 26722 - 58970 - 57546 - 25690 - 25696 - 986," & _
'"swdocmgr_previews - 11785 - 2051 - 64 - 17409 - 8598 - 34307 - 7 - 39552 - 6120 - 45838 - 36036 - 63312 - 53483 - 28563 - 8197 - 29994 - 14593 - 17070 - 52831 - 54805 - 53797 - 22937 - 36100 - 42449 - 38361 - 38237 - 40357 - 42401 - 40377 - 48461 - 54705 - 42449 - 47549 - 14337 - 26722 - 58970 - 57546 - 25690 - 25696 - 980," & _
'"swdocmgr_dimxpert -11785 - 2051 - 64 - 17409 - 8598 - 34307 - 7 - 1232 - 14732 - 49545 - 50049 - 46299 - 17983 - 18121 - 49159 - 20949 - 61201 - 55374 - 1785 - 38804 - 51561 - 24532 - 36100 - 42449 - 38361 - 38237 - 40357 - 42401 - 40377 - 48461 - 54705 - 42449 - 47549 - 14337 - 26722 - 58970 - 57546 - 25690 - 25696 - 984," & _
'"swdocmgr_geometry - 1178-57546-25690-25696-988,swdocmgr_xml-11785-02051-00064-17409-08598-34307-00007-59040-07523-17923-33807-44121-35092-54645-06151-37114-64182-41846-13168-26540-48525-23901-36100-42449-38361-38237-40357-42401-40377-48461-54705-42449-47549-14337-26722-58970-57546-25690-25696-980," & _
'"swdocmgr_tessellation -11785 - 2051 - 64 - 17409 - 8598 - 34307 - 7 - 43656 - 30591 - 47459 - 30474 - 55806 - 36894 - 15217 - 24581 - 32039 - 8378 - 40223 - 28467 - 10346 - 38141 - 24461 - 36100 - 42449 - 38361 - 38237 - 40357 - 42401 - 40377 - 48461 - 54705 - 42449 - 47549 - 14337 - 26722 - 58970 - 5"



Public swDmClassFactory As SwDocumentMgr.swDmClassFactory
Public swDmApp As SwDocumentMgr.SwDMApplication


Sub Property_writer()


    Dim i           As Integer
    Dim lastRow     As Long
    Dim myRng       As Range
    Dim mycell      As Range
    Dim MyColl      As Collection
    Dim myIterator  As Variant
    
    
    
    'Connect to the document manager
    ConnectToDm
    

    Set MyColl = New Collection

    MyColl.Add "modelpath"
    MyColl.Add "Another Value"

    lastRow = ActiveSheet.Cells.Find("*", SearchOrder:=xlByRows, SearchDirection:=xlPrevious).Row
    
    
    
    
    'Find folder,file and modelpath cols
    ' and process, process2, process3
    ' and configuration
    
    Dim Configuration_Col As Integer
    Dim Configuration_Col_Name As String
    Configuration_Col_Name = "configuration"

    
    Dim Folder_Col As Integer
    Dim File_Col As Integer
    Dim Modelpath_Col As Integer
        
    Dim Process_Col As Integer
    Dim Process2_Col As Integer
    Dim Process3_Col As Integer
    
    Dim Folder_Col_Name As String
    Dim File_Col_Name As String
    Dim Modelpath_Col_Name As String

    Dim Process_Col_Name As String
    Dim Process2_Col_Name As String
    Dim Process3_Col_Name As String
    
    Folder_Col_Name = "folder"
    File_Col_Name = "file"
    Modelpath_Col_Name = "modelpath"
    
    Process_Col_Name = "process"
    Process2_Col_Name = "process2"
    Process3_Col_Name = "process3"
    
    
        
    For i = 1 To 200
    
        If Cells(1, i) = Configuration_Col_Name Then
            Configuration_Col = i
        End If
        
        If Cells(1, i) = Folder_Col_Name Then
            Folder_Col = i
        End If
        
        If Cells(1, i) = File_Col_Name Then
            File_Col = i
        End If
        
        If Cells(1, i) = Modelpath_Col_Name Then
            Modelpath_Col = i
        End If
        
        If Cells(1, i) = Process_Col_Name Then
            Process_Col = i
        End If
        
        If Cells(1, i) = Process2_Col_Name Then
            Process2_Col = i
        End If
        
        If Cells(1, i) = Process3_Col_Name Then
            Process3_Col = i
        End If

    
    Next
    
    
    
    'Create the full path string and check if file exists
    Dim Check_Path_part As String
    Dim Check_Path_assy As String
    Dim result1 As String
    Dim result2 As String
    Dim result3 As String
    Dim result4 As String
    Dim result5 As String
    Dim result6 As String
    
    Dim checkstring As String
    Dim k As Integer
        
        
        
    
    Debug.Print "process col ", Process_Col
    Debug.Print "configuration col ", Configuration_Col
    
    
    Set myRng = Range(Cells(2, Modelpath_Col), Cells(lastRow, Modelpath_Col))
    For Each mycell In myRng
     'On Error Resume Next
        
        i = mycell.Row
        Check_Path_part = Cells(i, Folder_Col) & Cells(i, File_Col) & ".SLDPRT"
        Check_Path_assy = Cells(i, Folder_Col) & Cells(i, File_Col) & ".SLDASM"
        
        If FileExists(Check_Path_part) Then
            mycell.Value = Check_Path_part
        ElseIf FileExists(Check_Path_assy) Then
            mycell.Value = Check_Path_assy
        Else
            mycell.Value = "NO FILE"
        End If
        
        Debug.Print mycell.Value, Cells(i, Configuration_Col)
    Next
    
    'Debug.Print mycell.Value
    
    
    
    For Each mycell In myRng
        'SETSWPRP1 mycell.Value
        
        i = mycell.Row
        Debug.Print "process col "; Process_Col
        If FileExists(mycell.Value) Then
            Debug.Print Cells(i, 5)
            Debug.Print mycell.Value, Cells(i, Process_Col), Cells(i, Configuration_Col)
            
            result1 = WriteProp(mycell.Value, "Comments", Cells(i, Process_Col), Cells(i, Configuration_Col))
            result2 = WriteProp(mycell.Value, "process2", Cells(i, Process2_Col), Cells(i, Configuration_Col))
            result3 = WriteProp(mycell.Value, "process3", Cells(i, Process3_Col), Cells(i, Configuration_Col))

            End If
                    
        

        
    Next


End Sub



Function FileExists(ByVal FileToTest As String) As Boolean

   FileExists = (Dir(FileToTest) <> "")
End Function


Sub ConnectToDm()

    'Dim swDmClassFactory As SwDocumentMgr.swDmClassFactory
    'Dim swDmApp As SwDocumentMgr.SwDMApplication
    
    Set swDmClassFactory = CreateObject("SwDocumentMgr.SwDMClassFactory")
        
    If Not swDmClassFactory Is Nothing Then
        Set swDmApp = swDmClassFactory.GetApplication(SW_DM_KEY)
       
        Debug.Print "connected", swDmApp.GetLatestSupportedFileVersion
    Else
        Err.Raise vbError, "", "Document Manager SDK is not installed"
    End If
    
End Sub

Function OpenDocument(swDmApp As SwDocumentMgr.SwDMApplication, path As String, readOnly As Boolean) As SwDocumentMgr.SwDMDocument10
    
    Dim ext As String
    ext = LCase(Right(path, Len(path) - InStrRev(path, ".")))
    
    Dim docType As SwDmDocumentType
    
    Select Case ext
        Case "sldlfp"
            docType = swDmDocumentPart
        Case "sldprt"
            docType = swDmDocumentPart
        Case "sldasm"
            docType = swDmDocumentAssembly
        Case "slddrw"
            docType = swDmDocumentDrawing
        Case Else
            
            Err.Raise vbError, "", "Unsupported file type: " & ext
    End Select
    
    Dim swDmDoc As SwDocumentMgr.SwDMDocument10
    Dim openDocErr As SwDmDocumentOpenError
    Set swDmDoc = swDmApp.GetDocument(path, docType, readOnly, openDocErr)
    
    If swDmDoc Is Nothing Then
        Err.Raise vbError, "", "Failed to open document: '" & path & "'. Error Code: " & openDocErr
    End If
    
    Set OpenDocument = swDmDoc
    
End Function

Public Function GETSWPRP(fileName As String, prpName As String, Optional confName As String = "") As Variant
    
    'Dim swDmApp As SwDocumentMgr.SwDMApplication
    Dim swDmDoc As SwDocumentMgr.SwDMDocument10

        
    'Set swDmApp = ConnectToDm()
    Set swDmDoc = OpenDocument(swDmApp, fileName, True)
    
    Dim res As String
    Dim i As Integer
    
    
    Dim prpType As SwDmCustomInfoType
    
    
    If confName = "" Then

            res = swDmDoc.GetCustomProperty(prpName, prpType)
            


    Else
        Dim swDmConf As SwDocumentMgr.SwDMConfiguration10
'        activeconf = swDmDoc.ConfigurationManager.GetActiveConfigurationName
'        Set swDmConf = swDmDoc.ConfigurationManager.GetConfigurationByName(activeconf)
        
        Set swDmConf = swDmDoc.ConfigurationManager.GetConfigurationByName(confName)
        If Not swDmConf Is Nothing Then
        
                res = ""
                res = swDmConf.GetCustomProperty(prpName, prpType)

        Else
            Err.Raise vbError, "", "Failed to get configuration '" & confName & "' from '" & fileName & "'"
        End If
    End If
    
    GETSWPRP = res
    
    GoTo finally_
    
catch_:
    Debug.Print Err.Description
    Err.Raise Err.Number, Err.Source, Err.Description
finally_:
    If Not swDmDoc Is Nothing Then
        swDmDoc.CloseDoc
    End If

End Function

Sub SETSWPRP1(fileName As String)
Dim tet As String

tet = "fkdsalklj;salkjsfa"
Debug.Print tet, fileName

End Sub

Public Function WriteProp(fileName As String, prpName As String, prpVal As String, confName) As String
    
    'Dim swDmApp As SwDocumentMgr.SwDMApplication
    Dim swDmDoc As SwDocumentMgr.SwDMDocument10
    
    
       
    If TypeName(prpName) <> TypeName(prpVal) Then
        Err.Raise vbError, "", "Property name and value must be of the same type, e.g. either range or cell"
    End If
    
    'Set swDmApp = ConnectToDm()
    Set swDmDoc = OpenDocument(swDmApp, fileName, False)
    
'    'write the property to file level
    swDmDoc.AddCustomProperty prpName, swDmCustomInfoText, prpVal
    swDmDoc.SetCustomProperty prpName, prpVal
'
'    'write the property to conf level
    Dim swDmConf As SwDocumentMgr.SwDMConfiguration10
    
    'On Error Resume Next
    Set swDmConf = swDmDoc.ConfigurationManager.GetConfigurationByName(confName)
'
    If Not swDmConf Is Nothing Then
        swDmConf.AddCustomProperty prpName, swDmCustomInfoText, prpVal
        swDmConf.SetCustomProperty prpName, prpVal
    End If
'
    swDmDoc.Save
'    'SETSWPRP = "OK"
'
'    If Not swDmDoc Is Nothing Then
'        swDmDoc.CloseDoc
'    End If
'
End Function

Private Function RangeToArray(vRange As Variant) As Variant
    
    If TypeName(vRange) = "Range" Then
        Dim excelRange As Range
        Set excelRange = vRange
        
        Dim i As Integer
        
        Dim valsArr() As String
        ReDim valsArr(excelRange.Cells.Count - 1)
        
        i = 0
        
        For Each cell In excelRange.Cells
            valsArr(i) = cell.Value
            i = i + 1
        Next
        
        RangeToArray = valsArr
        
    Else
        Err.Raise vbError, "", "Value is not a Range"
    End If
    
End Function

