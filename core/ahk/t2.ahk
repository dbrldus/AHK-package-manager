#Requires AutoHotkey v2.0
#SingleInstance Force
#Include <AHKRPC2>
#Include <Path>

client := RPCManager(MAIN_IPC_PATH)

call(){
    MsgBox "Ping"
}

; client.regist(call, "ping")
; client.spin()
res := client.request("ping2", [], false)
MsgBox res