#Requires AutoHotkey v2.0
#SingleInstance Ignore
DetectHiddenWindows(true)

;#region Include 다 여기에

#Include <Path>
#Include <AHKRPC2>
; #Include <PythonFinder>
#Include <JSON_PLUS>
#Include <SafetyFileCheck>
;#endregion

;#region 파이썬 인터프리터 경로 설정
python_exe_path := PYTHON_EXE_PATH

;#endregion 

OnExit(cleanup)
setupPkgStatusJson() ; pkglist확인해서 pkgstatus와 비교 후, list 기반으로 stat 재작성.
;#region  RPC 통신을 위한 클라이언트 및 종료 신호 관리자 생성

client := RPCManager(PathJoin(TEMP_PATH, "ipc"))
client.regist(runPkgById, "runPkg")
client.regist(stopPkgById, "stopPkg")
client.regist(shutdown, "doShutdown")
client.spin()
;#endregion

Daniel := graveKeeper(client)
Daniel.cleanCorpse() ; 시작시 빠르게 정리
; SetTimer(() => Daniel.cleanCorpse(), 500)
; 허브 상태를 '활성'으로 변경하고 파일에 기록
hub_status := readJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"))
hub_status["is_active"] := "True"
writeJsonFile(PathJoin(RUNTIME_PATH, "hub-status.json"), hub_status)
; 상태 변경을 다른 GUI에 알림
client.request("doCheckHubStatus", [], true)

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

readPkgListJson() {
    return readJsonFile(PKG_LIST_FILE_PATH)
}

readPkgStatusJson() {
    return readJsonFile(PKG_STATUS_FILE_PATH)
}

setupPkgStatusJson() {
    ; pList: 기준이 되는 "마스터" 목록
    pList := readPkgListJson()

    ; pStat: 현재 상태 목록 (동기화 대상)
    pStat := readPkgStatusJson()

    ; --- 로직 시작 ---

    ; 1. 빠른 조회를 위해 각 리스트를 ID를 Key로 사용하는 Map으로 변환
    pListMap := Map()
    for pkg in pList {
        pListMap[pkg["id"]] := pkg ; 오류 수정: pkg.id -> pkg["id"]
    }

    pStatMap := Map()
    for pkg in pStat {
        pStatMap[pkg["id"]] := pkg ; 오류 수정: pkg.id -> pkg["id"]
    }

    ; 2. 동기화 결과를 담을 새로운 배열
    newPStat := []

    ; 3. 마스터 목록(pList)을 기준으로 최종 목록을 구성
    for id, masterPkg in pListMap {
        ; CASE 1: 현재 상태(pStat)에 이미 ID가 존재하는 경우
        if pStatMap.Has(id) {
            ; 요구사항: 정보 수정을 전혀 하지 않음
            ; 따라서 기존 pStat의 pkg를 아무런 변경 없이 그대로 가져와서 추가
            newPStat.Push(pStatMap[id])
        }
        ; CASE 2: 마스터 목록에는 있지만 현재 상태에 없는 경우
        else {
            ; 새로운 항목이므로 'stopped' 상태로 새로 만들어 추가
            newPStat.Push(Map(
                "id", masterPkg["id"],
                "process_name", 0,
                "creation_time", 0,
                "status", "stopped",
                "pid", -1
            ))
        }
    }

    ; pList에 없는 항목('P4')은 이 과정에서 newPStat에 추가되지 않으므로 자동으로 제거됨

    ; 4. 최종적으로 pStat을 새로운 리스트로 교체
    pStat := newPStat

    ; --- 결과 출력 ---
    ; finalResult := ""
    ; for pkg in pStat {
    ;     finalResult .= "id=" pkg["id"]
    ;         . "`nprocess_name=" pkg["process_name"]
    ;         . "`ncreation_time=" pkg["creation_time"]
    ;         . "`npid=" pkg["pid"]
    ;         . "`nstatus=" pkg["status"]
    ;         . "`n`n"
    ; }
    ; MsgBox finalResult
    writeJsonFile(PKG_STATUS_FILE_PATH, pStat)
}

/**
 * 외부 요청을 받아 특정 패키지(init_path)를 실행하는 함수.
 */
runPkgById(pkg_id) { ; id 받아서 패키지 경로 실행하고, 만약 됐으면 pid, 생성 시간 등 받아서 package-status에 기록, pid 리턴.
    init_path := PathJoin(PKGS_PATH, String(pkg_id), String(pkg_id) ".ahk")
    try {
        Run(init_path, , , &pid)
        getNameAndDtByPID(pid, &dt, &pName)
        setPkgStatusById(pkg_id, "running", pid, pName, dt)
        client.request("reloadGui", [], true)
        return pid
    } catch as e {
        throw Error("Fail to run pkg at:" init_path, "`n " (IsObject(e) ? e.Message : e))
    }
}

stopPkgById(pkg_id) { ; id 받아서 패키지 경로 종료 시도하고, 됐으면 스테이터스 수정, 0리턴
    init_path := String(pkg_id) ".ahk"
    targetHwnd := WinExist(init_path " ahk_class AutoHotkey")
    try {
        if (targetHwnd) {
            WinClose(targetHwnd)
            setPkgStatusById(pkg_id, "stopped", -1, 0, 0)
            client.request("reloadGui", [], true)
            return 0
        } else {
            MsgBox("ERROR: Fail to stop Pkg; ID: " pkg_id)
            return 1
        }
    }
}

setPkgStatusById(pkg_id, status, pid, pName, birth) {
    status_data := readPkgStatusJson()
    idx := findIndexById(status_data, pkg_id)
    status_data[idx]["status"] := status
    status_data[idx]["pid"] := pid
    status_data[idx]["process_name"] := pName
    status_data[idx]["creation_time"] := birth
    writeJsonFile(PKG_STATUS_FILE_PATH, status_data)
}

;#region Func def

hasid(arr, target) {
    for item in arr {
        if item.Has("id") && item["id"] = target
            return true
    }
    return false
}

findIndexById(arr, target) {
    for idx, item in arr {
        if item.Has("id") && item["id"] = target
            return idx
    }
    return 0  ; 못 찾았을 때는 0 (AHK 배열은 1부터 시작하니까)
}

findIndexByPid(arr, target) {
    for idx, item in arr {
        if item.Has("pid") && item["pid"] = target
            return idx
    }
    return 0  ; 못 찾았을 때는 0 (AHK 배열은 1부터 시작하니까)
}

getNameAndDtByPID(pid, &dt, &processName) {
    for process in ComObjGet("winmgmts:").ExecQuery("SELECT * FROM Win32_Process WHERE ProcessId=" pid) {
        ; WMI datetime → yyyyMMddHHmmss 형식
        raw := process.CreationDate
        dt := SubStr(raw, 1, 4) SubStr(raw, 5, 2) SubStr(raw, 7, 2) SubStr(raw, 9, 2) SubStr(raw, 11, 2) SubStr(raw, 13,
            2)
        processName := process.Name
    }
}
/**
 * 외부 종료 신호를 받았을 때 스크립트를 완전히 종료하는 함수.
 */
shutdown() {
    FileAppend("!!! SHUTDOWN FUNCTION CALLED !!!" "`n", A_ScriptDir "\shutdown_debug.log")
    ExitApp
}

class graveKeeper {
    __New(_communicator){
        this.client := _communicator
        SetTimer(() => this.cleanCorpse(), 333)
    }

    cleanCorpse(){
        pkgs_status := readPkgStatusJson()
        for pkg in pkgs_status{
            if(!this.isThisPkgWellBeing(pkg)){ ; 죽었으면
                setPkgStatusById(pkg["id"],"stopped",-1,0,0) ; 묻고
                this.client.request("reloadGui", [], true) ; 보고하기
            }
        }
    }

    isThisPkgWellBeing(pkg) {
        dt := 0
        processName := 0
        pkg_pid := pkg["pid"]
        if pkg_pid = -1{
            ; FileAppend("이미 싸늘함. `n", "*", "UTF-8-RAW")
            return true ; 중복 사망처리 안함.
        }
        getNameAndDtByPID(pkg_pid, &dt, &processName) 
        if dt = 0 && processName = 0{ ; pid가 정상이라면 여기서 실행 시간 나와야함
            ; ToolTip("Pid 죽음.`n")
            return false ; not well being : 프로세스가 존재하지 않는다
        }else If(processName = pkg["process_name"]){ ; ahk프로그램인지 확인
            if(Abs(Number(dt) - Number(pkg["creation_time"])) < 2){
                ; ToolTip "전부 정상. `n"
                return true ; 프로세스가 존재하고, ahk exe로 실행되었고, 실행 시간마저 시스템 기록과 json이 일치(1초 오차 이내)한다: 지극히 높은 확률로 우리가 실행한 패키지임.
            }else{
                ; ToolTip("Pid 있고 ahk 실행이지만 시스템 시간 다름.`n")
                return false ; 프로세스가 존재하고, ahk exe로 실행되었지만, 실행 시간이 시스템 기록과 다르다.
            }
        }else{
            ; ToolTip("Pid 정상이지만 ahk 아님.`n")
            return false ; ahk exe로 실행된 PID가 아니면 죽음: PID가 있지만 ahk가 아니다
        }
    }
}
; MsgBox StrSplit(A_AhkPath, "\").Pop()
