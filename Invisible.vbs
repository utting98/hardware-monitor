Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")
data = fso.OpenTextFile("FailCheck.txt").ReadLine()
int_data = CInt(data)
If int_data < 10 Then
Set WshShell = CreateObject("WScript.Shell") 
WshShell.Run chr(34) & "Restart.bat" & Chr(34), 0
Set WshShell = Nothing
Else
WScript.Quit
End If