; Run("notepad.exe", , , &pid)

getNameAndDtByPID(pid, &dt, &processName){
    for process in ComObjGet("winmgmts:").ExecQuery("SELECT * FROM Win32_Process WHERE ProcessId=" pid) {
        ; WMI datetime → yyyyMMddHHmmss 형식
        raw := process.CreationDate
        dt := SubStr(raw, 1, 4) SubStr(raw, 5, 2) SubStr(raw, 7, 2) SubStr(raw, 9, 2) SubStr(raw, 11, 2) SubStr(raw, 13, 2)
        processName := process.Name
    }
}
aaa:=0
bbb:=0

getNameAndDtByPID(26104, &aaa, &bbb)

MsgBox aaa " " bbb "`n" StrSplit(A_AhkPath, "\").Pop()

; setupPkgStatusJson()

setupPkgStatusJson() {
    ; pList: 기준이 되는 "마스터" 목록
    pList := [
        Map("id", "Latex", "name", "Latex Tools", "des", "whyy"),
        Map("id", "P2", "name", "Latex?", "des", "why242y"),
        Map("id", "P3", "name", "Lols", "des", "wy")
    ]

    ; pStat: 현재 상태 목록 (동기화 대상)
    pStat := [
        ; 'Latex'는 pList에도 있으므로 이 상태("running", pid: 1)가 그대로 유지되어야 함
        Map("id", "Latex", "process_name", "Latex Tools", "creation_time", "whyy", "status", "running", "pid", 1),
        ; 'P4'는 pList에 없으므로 제거되어야 함
        Map("id", "P4", "process_name", "To be removed", "creation_time", "why242y", "status", "running", "pid", 2)
    ]

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
                "process_name", "",
                "creation_time", "",
                "status", "stopped",
                "pid", -1
            ))
        }
    }

    ; pList에 없는 항목('P4')은 이 과정에서 newPStat에 추가되지 않으므로 자동으로 제거됨

    ; 4. 최종적으로 pStat을 새로운 리스트로 교체
    pStat := newPStat

    ; --- 결과 출력 ---
    finalResult := ""
    for pkg in pStat {
        finalResult .= "id=" pkg["id"]
            . "`nprocess_name=" pkg["process_name"]
            . "`ncreation_time=" pkg["creation_time"]
            . "`npid=" pkg["pid"]
            . "`nstatus=" pkg["status"]
            . "`n`n"
    }
    ; MsgBox finalResult
    
}
; MsgBox StrSplit(A_AhkPath, "\").Pop()  ; exe 파일 이름만 뽑음

; ; 혹은 전체 프로세스 목록에서 AHK만 추출
; for proc in ComObjGet("winmgmts:").ExecQuery("Select * from Win32_Process") {
;     if InStr(proc.Name, "AutoHotkey")
;         MsgBox proc.Name  ; 예: AutoHotkey64.exe
; }