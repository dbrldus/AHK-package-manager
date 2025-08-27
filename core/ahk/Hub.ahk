#Requires AutoHotkey v2.0
#Include <Path>
#Include <AHKRPC2>
#Include <PythonFinder>
#Include <JSON_PLUS>
#SingleInstance Force

cleanup(exitReason, exitCode) {
    global hub_status, RUNTIME_PATH, client
    try {
        hub_status["is_active"] := "False"
        writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
        client.request("doCheckHubStatus", [])
    } catch as e {
        try FileAppend(e.Message "`n", A_ScriptDir "\cleanup.log", "UTF-8")
    }
}
; -----------------------------------------------------------

python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
if (python_exe_path = ""){
    findPythonInterpreterGUI()
    python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
}
    


client := RPCManager(PathJoin(TEMP_PATH, "ipc"))
; client.request("doCheckHubStatus", [])
shutdownManager := RPCManager(PathJoin(TEMP_PATH, "shutdownSignal"))

runPkgInit(init_path) {
    try {
        Run(init_path, , , &pid)
        client.request("MovePkgRight", [])
        return pid
    } catch as e {
        throw Error("Fail to run pkg at: `n init_path, `n " (IsObject(e) ? e.Message : e))
    }
}

shutdown() {
    ; MsgBox "receieved shutdown signal!"
    ExitApp
}
client.regist(runPkgInit, "runPkgInit")
shutdownManager.regist(shutdown, "doShutdown")
shutdownManager.spin()
client.spin()

hub_status := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))
hub_status["is_active"] := "True"
writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
client.request("doCheckHubStatus", [])

^#D:: {
    client.request("MovePkgRight", [])
}
^#h:: {
    Run(A_ScriptFullPath)
}


; cleanup 함수가 이제 OnExit보다 위에 있으므로 오류가 발생하지 않습니다.
OnExit(cleanup)