#Requires AutoHotkey v2.0

AcquireServerLock(mutex_name, timeout_ms := 5000) {
    ; 강제 해제 확인
    lock_file := A_Temp "\" StrReplace(mutex_name, "\", "_") ".lock"
    if (FileExist(lock_file)) {
        try {
            lock_info := StrSplit(FileRead(lock_file), "`n")
            lock_pid := Integer(lock_info[1])
            lock_time := Integer(lock_info[2])

            ; 5분 초과 또는 프로세스 죽음 확인
            if (A_TickCount - lock_time > 300000 || !ProcessExist(lock_pid)) {
                FileDelete(lock_file)
                Sleep(100)
            }
        } catch {
            FileDelete(lock_file)
        }
    }

    ; 뮤텍스 생성
    mutex := DllCall("CreateMutexW", "ptr", 0, "int", true, "str", mutex_name, "ptr")
    if (!mutex)
        return false

    ; 이미 존재하면 대기
    if (DllCall("GetLastError") = 183) {
        result := DllCall("WaitForSingleObject", "ptr", mutex, "uint", timeout_ms)
        if (result != 0) {
            DllCall("CloseHandle", "ptr", mutex)
            return false
        }
    }

    ; 잠금 정보 저장
    try {
        FileAppend(DllCall("GetCurrentProcessId") . "`n" . A_TickCount, lock_file)
    }

    return mutex
}

ReleaseServerLock(mutex, mutex_name) {
    if (mutex) {
        ; 잠금 파일 삭제
        lock_file := A_Temp "\" StrReplace(mutex_name, "\", "_") ".lock"
        try {
            FileDelete(lock_file)
        }

        ; 뮤텍스 해제
        DllCall("ReleaseMutex", "ptr", mutex)
        DllCall("CloseHandle", "ptr", mutex)
    }
}