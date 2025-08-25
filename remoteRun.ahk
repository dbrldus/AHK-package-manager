#Requires AutoHotkey v2.0
#Include "C:\Users\acalo\OneDrive\문서\AutoHotkey\core\Lib\PyRPC.ahk"

client := RPCManager("C:\Users\acalo\OneDrive\문서\AutoHotkey\tmp")

client.spin()

::\run::{
    client.request("Run", [])
    ; MsgBox "run!"
}