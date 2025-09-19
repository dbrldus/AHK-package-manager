#SingleInstance Force
#NoTrayIcon
#Include <Path>
; #Include <PythonFinder>

python_exe_path := PYTHON_EXE_PATH

pyw := StrReplace(python_exe_path, "python.exe", "pythonw.exe")
^#g:: {
    obj := '"' pyw '"' " " '"' PathJoin(CORE_PATH, "py", "ManagerGUI.py") '"'
    Run obj, , , &pid   ; 실행 + PID 가져오기
    Sleep 500           ; 창 뜰 때까지 잠깐 대기
    if WinExist("ahk_pid " pid) {
        WinActivate                 ; 앞으로 가져오기
        WinSetAlwaysOnTop true      ; 항상 위 설정
    }
}
