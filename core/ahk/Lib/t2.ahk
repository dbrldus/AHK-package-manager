#Requires AutoHotkey v2.0

#Include AHKRPC.ahk

cli := RPCManager(A_ScriptDir)
Active(x){
    MsgBox(x ", Hi!")
}

cli.regist(Active, "Active")
cli.spin()