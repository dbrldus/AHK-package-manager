#Requires AutoHotkey v2.0
#Include <Path>
#Include <JSON_PLUS>
#SingleInstance Ignore
Run(HUB_PATH, , ,&pid)

stat := readJsonFile(HUB_STATUS_FILE_PATH)

stat["PID"] := pid

writeJsonFile(HUB_STATUS_FILE_PATH, stat)

ExitApp