Option Explicit
Dim fso, shell
Dim folder, pythonExe, python2Exe, appFile
Dim linkFile, ipconfigFile
Dim localURL, networkURL
Dim cmd, file, output
Dim line, ip

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
pythonExe = folder & "\.venv\Scripts\python.exe"
python2Exe = folder & "\python314\python.exe"
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

' --- pobierz adres IP sieciowy ---
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

' --- helper: uruchom polecenie i pobierz stdout ---
Function RunAndGetOutput(command)
    Dim exec, out, s
    On Error Resume Next
    Set exec = shell.Exec("cmd.exe /c " & command)
    If Err.Number <> 0 Then
        RunAndGetOutput = ""
        Exit Function
    End If
    On Error GoTo 0
    out = ""
    Do While Not exec.StdOut.AtEndOfStream
        s = exec.StdOut.ReadLine
        out = out & s & vbCrLf
    Loop
    RunAndGetOutput = out
End Function

Function NormalizePath(p)
    If IsNull(p) Then
        NormalizePath = ""
        Exit Function
    End If
    p = Trim(p)
    p = Replace(p, """", "")
    p = Replace(p, "/", "\")
    NormalizePath = LCase(p)
End Function

' --- pobierz szczegóły procesu (ExecutablePath i CommandLine) - próbuj PowerShell, fallback WMIC ---
Function GetProcessDetails(pid)
    Dim out, lines, i, found, execPath, cmdLine, part
    execPath = ""
    cmdLine = ""
    found = False

    ' PowerShell attempt (modern, preferowany)
    out = RunAndGetOutput("powershell -NoProfile -Command ""$p=Get-CimInstance Win32_Process -Filter 'ProcessId=" & pid & "'; if ($p) { if ($p.ExecutablePath) { Write-Output $p.ExecutablePath } else { Write-Output '' }; Write-Output '---CMD---'; if ($p.CommandLine) { Write-Output $p.CommandLine } else { Write-Output '' } }""")
    If Trim(out) <> "" Then
        lines = Split(out, vbCrLf)
        For i = 0 To UBound(lines)
            lines(i) = Trim(lines(i))
        Next
        ' szukamy markeru ---CMD---
        For i = 0 To UBound(lines)
            If lines(i) = "---CMD---" Then
                If i >= 1 Then execPath = lines(i-1)
                If i+1 <= UBound(lines) Then cmdLine = lines(i+1)
                found = True
                Exit For
            End If
        Next
    End If

    ' fallback: WMIC (starsze systemy)
    If Not found Then
        out = RunAndGetOutput("wmic process where ProcessId=" & pid & " get ExecutablePath,CommandLine /VALUE")
        If Trim(out) <> "" Then
            lines = Split(out, vbCrLf)
            For i = 0 To UBound(lines)
                part = Trim(lines(i))
                If LCase(Left(part, 14)) = "executablepath" Then
                    execPath = Mid(part, InStr(part, "=") + 1)
                ElseIf LCase(Left(part, 11)) = "commandline=" Then
                    cmdLine = Mid(part, InStr(part, "=") + 1)
                End If
            Next
            If execPath <> "" Or cmdLine <> "" Then found = True
        End If
    End If

    GetProcessDetails = execPath & vbCrLf & cmdLine
End Function

' --- sprawdź czy ktoś nasłuchuje na porcie 8501 ---
Dim netstatOut, lines, i, foundLine, tokens, pid
netstatOut = RunAndGetOutput("netstat -ano | findstr LISTENING | findstr :8501")
pid = ""
If Trim(netstatOut) <> "" Then
    lines = Split(netstatOut, vbCrLf)
    For i = 0 To UBound(lines)
        If Trim(lines(i)) <> "" Then
            foundLine = Trim(lines(i))
            tokens = Split(foundLine)
            If UBound(tokens) >= 0 Then
                pid = tokens(UBound(tokens))
                Exit For
            End If
        End If
    Next
End If

' --- zapisz link.txt ---
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

If pid = "" Then
    ' port wolny -> uruchom aplikację (bez --server.address i --server.port)
    cmd = """" & pythonExe & """ -m streamlit run """ & appFile & """"
    shell.Run cmd, 0, False
    WScript.Sleep 2000
    shell.Run localURL, 1, False
    Set shell = Nothing
    Set fso = Nothing
    WScript.Quit 0
Else
    ' jest jakiś proces na porcie -> sprawdź co to
    Dim taskOut, procImage, taskLines, tline, parts, details, execPath, cmdLine
    taskOut = RunAndGetOutput("tasklist /FI ""PID eq " & pid & """ /FO CSV /NH")
    procImage = ""
    If Trim(taskOut) <> "" Then
        taskLines = Split(taskOut, vbCrLf)
        tline = Trim(taskLines(0))
        If tline <> "" Then
            parts = Split(tline, ",")
            If UBound(parts) >= 0 Then
                procImage = Replace(parts(0), """", "")
            End If
        End If
    End If

    Dim isPythonProc
    isPythonProc = False
    If LCase(procImage) = "python.exe" Or LCase(procImage) = "pythonw.exe" Then
        isPythonProc = True
    End If

    If Not isPythonProc Then
        Dim occupier
        If procImage <> "" Then
            occupier = procImage & " (PID " & pid & ")"
        Else
            occupier = "PID " & pid
        End If
        MsgBox "Port 8501 jest już zajęty przez proces: " & occupier & vbCrLf & _
               "Aplikacja NIE zostanie uruchomiona. Nie zabijam procesu.", vbExclamation
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    ' pobierz ExecutablePath i CommandLine procesu
    details = GetProcessDetails(pid)
    Dim tmpArr
    tmpArr = Split(details, vbCrLf, 2)
    execPath = ""
    cmdLine = ""
    If UBound(tmpArr) >= 0 Then execPath = Trim(tmpArr(0))
    If UBound(tmpArr) = 1 Then cmdLine = Trim(tmpArr(1))

    execPath = NormalizePath(execPath)
    cmdLine = LCase(Trim(cmdLine))
    Dim expectedPython, expected2Python, expectedApp
    expectedPython = NormalizePath(pythonExe)
    expected2Python = NormalizePath(python2Exe)
    expectedApp = LCase(Trim(appFile))

    ' sprawdź, czy ExecutablePath dokładnie odpowiada naszemu .venv\Scripts\python.exe
    If execPath = "" Then
        MsgBox "Nie udało się odczytać ExecutablePath procesu PID " & pid & ". Nie zabijam procesu.", vbExclamation
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    If execPath <> expectedPython And execPath <> expected2Python Then
        MsgBox "Proces na porcie 8501 (PID " & pid & ") uruchomiony jest przy pomocy interpretera: " & execPath & vbCrLf & _
               "To NIE jest oczekiwane .venv\Scripts\python.exe (" & expectedPython & ") ani (" & expected2Python & "). Nie zabijam procesu.", vbExclamation
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    ' sprawdź, czy CommandLine zawiera dokładnie ścieżkę do naszego app.py
    If cmdLine = "" Then
        MsgBox "Nie udało się odczytać CommandLine procesu PID " & pid & ". Nie zabijam procesu.", vbExclamation
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    If InStr(1, cmdLine, expectedApp, vbTextCompare) = 0 Then
        MsgBox "Proces PID " & pid & " jest interpreterem " & execPath & " ale jego command line nie zawiera oczekiwanej ścieżki do app.py:" & vbCrLf & _
               cmdLine & vbCrLf & "Nie zabijam procesu.", vbExclamation
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    ' Wszystko się zgadza -> zabijamy naszą aplikację i uruchamiamy ponownie
    Dim taskkillCmd, ret, confirmOut
    taskkillCmd = "taskkill /PID " & pid & " /T /F"
    ret = shell.Run("cmd.exe /c " & taskkillCmd, 0, True)
    If ret <> 0 Then
        MsgBox "Nie udało się zakończyć procesu PID " & pid & " (kod: " & ret & "). Aplikacja NIE została uruchomiona.", vbCritical
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    ' sprawdź czy proces zniknął
    confirmOut = RunAndGetOutput("tasklist /FI ""PID eq " & pid & """ /NH")
    If InStr(1, LCase(confirmOut), "no tasks are running", vbTextCompare) = 0 Then
        ' wciąż istnieje
        MsgBox "Proces PID " & pid & " nadal działa. Nie uruchamiam nowej instancji.", vbExclamation
        Set shell = Nothing
        Set fso = Nothing
        WScript.Quit 1
    End If

    ' uruchom nową instancję
    cmd = """" & pythonExe & """ -m streamlit run """ & appFile & """"
    shell.Run cmd, 0, False
    WScript.Sleep 2000
    shell.Run localURL, 1, False
    Set shell = Nothing
    Set fso = Nothing
    WScript.Quit 0
End If
