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
HUB_PATH := PathJoin(CORE_PATH,"ahk","Hub.ahk")
HUB_STATUS_FILE_PATH := PathJoin(RUNTIME_PATH, "hub-status.json")
PKG_STATUS_FILE_PATH := PathJoin(RUNTIME_PATH, "package-status.json")
PKG_LIST_FILE_PATH := PathJoin(SCHEMA_PATH, "package-list.json")
MAIN_IPC_PATH := PathJoin(TEMP_PATH, "ipc")
if !DirExist(MAIN_IPC_PATH) {
    DirCreate(MAIN_IPC_PATH)
}
; 확인용
; MsgBox(CORE_PATH)

fileAutoGen(filepath) {
    ; 파일이 이미 존재하면 아무것도 안 함
    if FileExist(filepath)
        return true

    ; 디렉토리 경로 추출
    SplitPath(filepath, , &dir_path)

    ; 디렉토리가 없으면 생성 (재귀적으로 모든 상위 디렉토리 생성)
    if dir_path && !DirExist(dir_path) {
        try {
            DirCreate(dir_path)
        } catch as e {
            ; MsgBox("디렉토리 생성 실패: " e.Message)
            return false
        }
    }

    ; 빈 파일 생성
    try {
        FileAppend("", filepath)
        return true
    } catch as e {
        ; MsgBox("파일 생성 실패: " e.Message)
        return false
    }
}

PYTHON_EXE_PATH := PathJoin(SCHEMA_PATH, "PYTHON3.12.6", "python.exe")