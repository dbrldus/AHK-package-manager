#Requires AutoHotkey v2.0
#SingleInstance Ignore

;#region Include 다 여기에

#Include <Path>
#Include <AHKRPC2>
#Include <PythonFinder>
#Include <JSON_PLUS>
;#endregion 

;#region 파이썬 인터프리터 경로 설정
python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
if (python_exe_path = "") {
    findPythonInterpreterGUI()
    python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
}
;#endregion 
; RPC 통신을 위한 클라이언트 및 종료 신호 관리자 생성
client := RPCManager(PathJoin(TEMP_PATH, "ipc"))

OnExit(cleanup)


client.regist(runPkgById, "runPkgInit")
client.regist(shutdown, "doShutdown")


FileAppend("=== CALLBACKS REGISTERED ===" "`n", A_ScriptDir "\hub_debug.log")
for name, funcc in client.callbacks {
    FileAppend("Registered: " name "`n", A_ScriptDir "\hub_debug.log")
}

; 허브 상태를 '활성'으로 변경하고 파일에 기록
hub_status := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))
hub_status["is_active"] := "True"
writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
; 상태 변경을 다른 GUI에 알림
client.request("doCheckHubStatus", [], true)
client.spin()


; ====================================================================
; 4. 함수 정의
; ====================================================================
/**
 * 스크립트가 종료될 때 호출되는 정리 함수.
 */
; MsgBox "!!!"
cleanup(exitReason, exitCode) {
    global hub_status, RUNTIME_PATH, client
    try {
        hub_status["is_active"] := "False"
        writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
        client.request("doCheckHubStatus", [], true)

    } catch as e {
        try FileAppend(e.Message "`n", A_ScriptDir "\cleanup.log", "UTF-8")
    }
}

/**
 * 외부 요청을 받아 특정 패키지(init_path)를 실행하는 함수.
 */
runPkgById(id) {
    init_path := PathJoin(PKGS_PATH, String(id), "init.ahk")
    try {
        Run(init_path, , , &pid)
        client.request("reloadGui", [], true)
        return pid
    } catch as e {
        throw Error("Fail to run pkg at: `n init_path, `n " (IsObject(e) ? e.Message : e))
    }
}

/**
 * 외부 종료 신호를 받았을 때 스크립트를 완전히 종료하는 함수.
 */
shutdown() {
    FileAppend("!!! SHUTDOWN FUNCTION CALLED !!!" "`n", A_ScriptDir "\shutdown_debug.log")
    ExitApp
}

; ====================================================================
; 5. 핫키 정의
; ====================================================================
; 패키지 이동 요청
