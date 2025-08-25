; MyScript.ahk
#Requires AutoHotkey v2.0
#Include <PyRPC>
#SingleInstance Force
client := RPCManager(A_ScriptDir "\..\tmp")
runPkgInit(init_path){
    Run(init_path)
    return 0
}
client.regist(runPkgInit, "runPkgInit")
client.spin()

F1::{
    result := client.request("multiply", [22, 3])
    MsgBox("Python result: " result)
}
^#H::{
    Run("C:\Users\acalo\OneDrive\문서\AutoHotkey\core\Hub.ahk")
}
^#g::{
    Run("C:\Users\acalo\OneDrive\문서\AutoHotkey\core\ManagerGUI.py")
}
