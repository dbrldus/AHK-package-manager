#SingleInstance Force
#NoTrayIcon
#Include <Path>
#Include <PythonFinder>

python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
if (python_exe_path = "") {
    findPythonInterpreterGUI()
    python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
}
pyw := StrReplace(python_exe_path, "python.exe", "pythonw.exe")

^#g:: {
    obj := '"' pyw '"' " " '"' PathJoin(CORE_PATH, "py", "DummyGUI copy.py") '"'
    Run obj
}