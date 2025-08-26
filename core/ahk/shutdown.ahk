#Requires AutoHotkey v2.0
#Include <JSON_PLUS>
#Include <Path>
#Include <AHKRPC>
#SingleInstance Force

shutdownClient := RPCManager(PathJoin(TEMP_PATH, "shutdownSignal"))

; stat := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))

; pid := stat["PID"]

; stat["PID"] := -1

; writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), stat)

try {
    shutdownClient.request("doShutdown", [])
} catch {
    MsgBox "종료 실패 " ;pid
}

hub_status := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))
hub_status["is_active"] := "False"
writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
client := RPCManager(PathJoin(TEMP_PATH, "ipc"))
client.request("doCheckHubStatus", [])
ExitApp
