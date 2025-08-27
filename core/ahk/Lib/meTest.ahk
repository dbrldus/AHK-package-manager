#Requires AutoHotkey v2.0
; === 아주 단순한 Mutual Exclusion (파일 독점 잠금) ===
; CS_PATH 파일을 "공유 없음"으로 열어서 잠금 → 작업 → 닫기

CS_PATH := A_Temp "\critical.txt"   ; 크리티컬 섹션(대상 파일 경로)
DEMO_ID := A_Args.Length ? A_Args[1] : A_TickCount  ; 데모 표식

; 파일 잠금 획득 (타임아웃 ms)
AcquireExclusiveFile(path, timeout_ms := 10000) {
    deadline := A_TickCount + timeout_ms
    while true {
        ; CreateFileW(path, GENERIC_READ|GENERIC_WRITE, share=0, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL)
        h := DllCall("CreateFile", "str", path, "uint", 0xC0000000, "uint", 0, "ptr", 0, "uint", 4, "uint", 0x80, "ptr", 0, "ptr")
        if (h != -1)   ; INVALID_HANDLE_VALUE = -1
            return FileOpen(h, "h")  ; 핸들 래핑(닫으면 자동 해제)
        if (A_TickCount >= deadline)
            throw Error("lock timeout: " path)
        Sleep 20
    }
}

; ============== 데모: 임계구역 ==============
try {
    f := AcquireExclusiveFile(CS_PATH, 10000)  ; 잠금 획득
    ; ---- 크리티컬 섹션 시작 ----
    ; 여기서만 파일에 쓰기/읽기 수행
    FileAppend(Format("[{1}] ENTER`n", DEMO_ID), "*")   ; 콘솔 표시(콘솔에서 실행 시)
    loop 5 {
        f.WriteLine(Format("[{1}] step {2}", DEMO_ID, A_Index))
        f.Flush()
        Sleep 200
    }
    FileAppend(Format("[{1}] LEAVE`n", DEMO_ID), "*")
    ; ---- 크리티컬 섹션 끝 ----
} catch as e {
    MsgBox "lock failed: " e.Message
} finally {
    try f.Close()
}