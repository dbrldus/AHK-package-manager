#Requires AutoHotkey v2.0
#Include <Path>
#Include <AHKRPC2>

client := RPCManager(MAIN_IPC_PATH)


target := client.request("doShutdown", [], true)

; MsgBox target