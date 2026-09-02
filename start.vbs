Option Explicit
Dim fso, shell
Dim folder, pythonExe, appFile
Dim linkFile, ipconfigFile
Dim localURL, networkURL
Dim cmd, file, output
Dim line, ip
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = folder & "\.venv\Scripts\python.exe"
appFile = folder & "\app.py"
linkFile = folder & "\link.txt"
ipconfigFile = folder & "\ipconfig_temp.txt"
If Not fso.FileExists(pythonExe) Then
    MsgBox "Brak Pythona:" & vbCrLf & pythonExe, vbCritical
    WScript.Quit 1
End If
If Not fso.FileExists(appFile) Then
    MsgBox "Brak aplikacji:" & vbCrLf & appFile, vbCritical
    WScript.Quit 1
End If
localURL = "http://localhost:8501"
networkURL = "Nie znaleziono adresu IPv4"
cmd = "cmd.exe /c ipconfig > """ & ipconfigFile & """"
shell.Run cmd, 0, True
If fso.FileExists(ipconfigFile) Then
    Set file = fso.OpenTextFile(ipconfigFile, 1, False)
    Do Until file.AtEndOfStream
        line = Trim(file.ReadLine)
        If InStr(1, line, "IPv4", vbTextCompare) > 0 Then
            If InStr(line, ":") > 0 Then
                ip = Trim(Mid(line, InStrRev(line, ":") + 1))
                If ip <> "" And Left(ip, 3) <> "127" Then
                    networkURL = "http://" & ip & ":8501"
                    Exit Do
                End If
            End If
        End If
    Loop
    file.Close
    Set file = Nothing
    fso.DeleteFile ipconfigFile, True
End If
Set output = fso.CreateTextFile(linkFile, True)
output.WriteLine "WIZUALIZACJA BAZY DANYCH"
output.WriteLine "======================"
output.WriteLine ""
output.WriteLine "Local URL:"
output.WriteLine localURL
output.WriteLine ""
output.WriteLine "Network URL:"
output.WriteLine networkURL
output.Close
Set output = Nothing
cmd = """" & pythonExe & """ -m streamlit run """ & appFile & _
      """ --server.address=0.0.0.0 --server.port=8501"
shell.Run cmd, 0, False
WScript.Sleep 2000
shell.Run localURL, 1, False
Set shell = Nothing
Set fso = Nothing
