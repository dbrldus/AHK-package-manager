#Requires AutoHotkey v2.0
#SingleInstance Ignore

/*
 * ====================================================================
 * 이 스크립트는 외부 RPC 요청을 받아 패키지를 실행하고,
 * 상태를 관리하는 허브(Hub) 역할을 합니다.
 * ====================================================================
*/

; ====================================================================
; 1. 스크립트 설정 및 라이브러리 포함
; ====================================================================
#Include <Path>
#Include <AHKRPC2>
#Include <PythonFinder>
#Include <JSON_PLUS>

; ====================================================================
; 2. 초기화 (변수 및 객체 생성)
; ====================================================================
; Python 인터프리터 경로 확인
python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
if (python_exe_path = "") {
    findPythonInterpreterGUI()
    python_exe_path := FileRead(SCHEMA_PATH "\python_interpreter_path.txt")
}

; RPC 통신을 위한 클라이언트 및 종료 신호 관리자 생성
client := RPCManager(PathJoin(TEMP_PATH, "ipc"))

; ====================================================================
; 3. 핵심 실행 로직 (스크립트 시작 시 자동 실행)
; ====================================================================
; 스크립트 종료 시 'cleanup' 함수가 호출되도록 최우선으로 등록
OnExit(cleanup)

; RPC를 통해 외부에서 호출할 함수들을 등록
client.regist(runPkgInit, "runPkgInit")
client.regist(shutdown, "doShutdown")



FileAppend("=== CALLBACKS REGISTERED ===" "`n", A_ScriptDir "\hub_debug.log")
for name, funcc in client.callbacks {
    FileAppend("Registered: " name "`n", A_ScriptDir "\hub_debug.log")
}

; 허브 상태를 '활성'으로 변경하고 파일에 기록
hub_status := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))
hub_status["is_active"] := "True"
writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)

; 상태 변경을 다른 프로세스에 알림
client.request("doCheckHubStatus", [], true)

; 모든 준비가 끝났으므로, 외부의 종료 신호를 무한정 기다림
; 이 함수가 호출되면 스크립트는 여기에서 대기 상태에 들어감
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
runPkgInit(init_path) {
    try {
        Run(init_path, , , &pid)
        client.request("MovePkgRight", [])
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
