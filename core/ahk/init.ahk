#Requires AutoHotkey v2.0
#Include <Path>
#Include <JSON_PLUS>
#SingleInstance Force

stat := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))

Run(PathJoin(CORE_PATH, "ahk", "Hub.ahk"), , ,&pid)

stat["PID"] := pid

writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), stat)

; MsgBox "INIT!!"

ExitApp