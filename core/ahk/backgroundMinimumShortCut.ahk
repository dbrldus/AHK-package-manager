#SingleInstance Force
#NoTrayIcon
#Include <Path>
#Include <PythonFinder>

python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
if (python_exe_path = "") {
    findPythonInterpreterGUI()
    python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
}

^#g:: {
    obj := '"' python_exe_path '"' " " '"' PathJoin(CORE_PATH, "py", "ManagerGUI.py") '"'
    Run obj
}