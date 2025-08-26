#Requires AutoHotkey v2.0
#Include JSON.ahk
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