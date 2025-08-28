#Requires AutoHotkey v2.0

#Include <AHKRPC2>
#Include <Path>

client := RPCManager(MAIN_IPC_PATH)


client.request("ping",[2,3222,4,5],true)
