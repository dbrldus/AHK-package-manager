; 프로젝트 루트 찾기 (예시: .ANCHOR 파일 기반)
FindProjectRoot(startPath := A_ScriptDir) {
    cur := startPath
    loop {
        if FileExist(cur "\.ANCHOR")
            return cur
        pos := InStr(cur, "\", , -1)
        if !pos
            break
        parent := SubStr(cur, 1, pos - 1)
        if (parent = "" || parent = cur)
            break
        cur := parent
    }
    return A_ScriptDir
}

PathJoin(parts*) {
    path := ""
    for i, p in parts {
        if (path = "")
            path := RTrim(p, "\/")
        else
            path .= "\" Trim(p, "\/")
    }
    return path
}

; --- 상수 정의 ---
ROOT_PATH := FindProjectRoot()
CORE_PATH := ROOT_PATH "\core"
DATA_PATH := ROOT_PATH "\data"
CONFIG_PATH := ROOT_PATH "\config"
RUNTIME_PATH := CORE_PATH "\runtime"
if !DirExist(RUNTIME_PATH) {
    DirCreate(RUNTIME_PATH)
}
defaultJson := "[]"
json_file := PathJoin(RUNTIME_PATH, "package-status.json")
if !FileExist(json_file) {
    try {
        FileAppend(defaultJson, json_file, "UTF-8")
    }
}

defaultJson := '{"is_active":"False", "PID": -1}'
json_file := PathJoin(RUNTIME_PATH, "hub-status.json")
if !FileExist(json_file) {
    try {
        FileAppend(defaultJson, json_file, "UTF-8")
    }
}
SCHEMA_PATH := CORE_PATH "\schema"
TEMP_PATH := CORE_PATH "\tmp"
ASSETS_PATH := ROOT_PATH "\assets"
ICONS_PATH := ASSETS_PATH "\icons"
PKGS_PATH := PathJoin(ROOT_PATH, "packages")

; 확인용
; MsgBox(CORE_PATH)
