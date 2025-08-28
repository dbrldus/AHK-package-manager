#Requires AutoHotkey v2.0
#Include Path.ahk
#Include JSON_PLUS.ahk
#Include AHKRPC2.ahk
#SingleInstance Ignore

pkg_json_path := A_ScriptDir "\package.json"

packageInfo := readJsonFile(pkg_json_path)
packageId := packageInfo["id"]

status_data := readJsonFile(PKG_STATUS_FILE_PATH)

if (hasid(status_data, packageId)) {
    status_data[findIndexByid(status_data, packageId)]["status"] := "running"
} else {
    obj := Map("id", packageId, "status", "running")
    status_data.Push(obj)
}

writeJsonFile(PKG_STATUS_FILE_PATH, status_data)



;#region Func def

hasid(arr, target) {
    for item in arr {
        if item.Has("id") && item["id"] = target
            return true
    }
    return false
}

findIndexByid(arr, target) {
    for idx, item in arr {
        if item.Has("id") && item["id"] = target
            return idx
}
return 0  ; 못 찾았을 때는 0 (AHK 배열은 1부터 시작하니까)
}

Run(PathJoin(A_ScriptDir, packageInfo["id"]) ".ahk")

;#endregion 