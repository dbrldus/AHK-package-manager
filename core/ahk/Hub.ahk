; MyScript.ahk
#Requires AutoHotkey v2.0
#Include <Path>
#Include <AHKRPC>
#Include <PythonFinder>
#Include <JSON_PLUS>
#SingleInstance Force



python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
if (python_exe_path = "")
    findPythonInterpreterGUI()
    python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")


client := RPCManager(PathJoin(TEMP_PATH, "ipc"))
runPkgInit(init_path){
    try {
        Run(init_path, , , &pid)
        client.request("MovePkgRight", [])
        return pid
    } catch as e {
        throw Error("Fail to run pkg at: `n init_path, `n " (IsObject(e) ? e.Message : e))
    }
}

isWell(init_path) {
    return 0
}
client.regist(runPkgInit, "runPkgInit")
client.regist(isWell, 'asdsad')
client.spin()


client.request("doCheckHubStatus", [])

^#D::{
    client.request("MovePkgRight", [])
}
^#h::{
    Run(A_ScriptFullPath)
}
^#g::{
    obj := '"' python_exe_path '"' " " '"' PathJoin(CORE_PATH, "py", "ManagerGUI.py") '"'
    Run obj
}

cleanup(){
    return 0
}

OnExit(cleanup)
