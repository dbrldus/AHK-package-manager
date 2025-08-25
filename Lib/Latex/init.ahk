#Requires AutoHotkey v2.0
#Include ..\JSON.ahk

pkg_json_path := A_ScriptDir "\package.json"
status_path := A_ScriptDir "\..\..\core\package-status.json"

packageInfo := readJsonFile(pkg_json_path)
packageName := packageInfo["name"]
Run(A_ScriptDir "\" packageInfo["id"] ".ahk")

status_data := readJsonFile(status_path)

if(hasName(status_data, packageName)){
    status_data[findIndexByName(status_data, packageName)]["is_active"] := "True"
}else{ 
    obj := Map("name", packageName, "is_active", "True")
    status_data.Push(obj)
    MsgBox "pushed!"
}
writeJsonFile(status_path, status_data)
; MsgBox "Latex init Active!"

readJsonFile(path) {
    json_script := FileOpen(path, "r")
    txt := json_script.Read()
    data := Jxon_Load(&txt)
    return data
}
writeJsonFile(path, obj) {
    json_script := FileOpen(path, "w")
    json_script.Write(Jxon_Dump(obj))
    return 0
}
hasName(arr, target) {
    for item in arr {
        if item.Has("name") && item["name"] = target
            return true
    }
    return false
}

findIndexByName(arr, target) {
    for idx, item in arr {
        if item.Has("name") && item["name"] = target
            return idx
    }
    return 0  ; 못 찾았을 때는 0 (AHK 배열은 1부터 시작하니까)
}