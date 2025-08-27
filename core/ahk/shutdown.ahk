#Requires AutoHotkey v2.0
#Include <JSON_PLUS>
#Include <Path>
#Include <AHKRPC2>
#SingleInstance Ignore 

client := RPCManager(MAIN_IPC_PATH)

; stat := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))

; pid := stat["PID"]

; stat["PID"] := -1

; writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), stat)

try {
    client.request("doShutdown", [], true)
} catch {
    MsgBox "종료 실패 " ;pid
}

; hub_status := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))
; hub_status["is_active"] := "False"
; writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
client.request("doCheckHubStatus", [])
ExitApp
