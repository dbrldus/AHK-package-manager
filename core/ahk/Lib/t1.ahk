#Requires AutoHotkey v2.0

#Include AHKRPC.ahk

cli := RPCManager(A_ScriptDir)

cli.request("MovePkgRight", [])