#Requires AutoHotkey v2.0
#SingleInstance force
#Include <AHKRPC2>
#Include <Path>
; Persistent()

client := RPCManager(MAIN_IPC_PATH)

myCallback(x, y){
    MsgBox x + y " get!"
    return x + y
}

Ping(){
    MsgBox "Ping!!!"
}

shd(){
    ExitApp
}

client.regist(myCallback, "call")
client.regist(Ping, "ping")
client.regist(shd, "shutdown")

; client.request("demo",[],1)
client.check()

