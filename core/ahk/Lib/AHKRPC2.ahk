#Requires AutoHotkey v2.0
#Include Path.ahk
; 상호 배제 기본 연산을 위한 요구사항
; 상호 배제를 구현하기 위해선 아래 세 가지 조건을 만족해야 합니다.

; 1. Mutual exclusion (상호 배제)
; CS에 프로세스가 있으면, 다른 프로세스의 진입을 금지하게 합니다.

; 2. Progress (진행)
; CS안에 프로세스가 없다면 CS에 진입할 수 있어야 합니다.

; 3. Bounded waiting (유한한 대기)
; 프로세스의 CS 진입은 유한 시간 내에 허용되어야 합니다.
; 계속 기다리는 상황을 만들지 말고 언젠간 들어갈 수 있게 하여 기아상태(starvation) 를 방지합니다.

class RPCManager {
    __New(communication_path) {
        this.callbacks := Map()
        this.running := false
        this.temp_path := communication_path
        this.request_queue := communication_path "\rpc_requests.queue"
        this.server_mutex_name := "RPCServer_" StrReplace(communication_path, "\", "_")
        this.ENCODING := 'UTF-8-RAW'
        ; 큐 파일이 없으면 생성
        fileAutoGen(this.request_queue)
    }

    AcquireServerLock(timeout_ms := 1000) {
        mutex := DllCall("CreateMutex", "ptr", 0, "int", false, "str", this.server_mutex_name, "ptr")
        if !mutex
            return false

        result := DllCall("WaitForSingleObject", "ptr", mutex, "uint", timeout_ms)
        if (result = 0) {  ; WAIT_OBJECT_0
            return mutex
        } else {
            DllCall("CloseHandle", "ptr", mutex)
            return false
        }
    }

    ReleaseServerLock(mutex) {
        if mutex {
            DllCall("ReleaseMutex", "ptr", mutex)
            DllCall("CloseHandle", "ptr", mutex)
        }
    }

    GenerateID(len) {
        ; 랜덤 ID 생성 (16자리)
        chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        id := ""
        loop len {
            r := Random(1, StrLen(chars))  ; 1 ~ 길이 사이 정수
            id .= SubStr(chars, r, 1)      ; r번째 글자 1개 추출
        }
        return id
    }

    request(callback_name, params := [], ignore_response := false) { ;서비스 이름, 파라미터 받아서 rpc_res_id.txt 나올 때까지 5초 대기, 없으면 rpc_res_id.txt
        ; 고유 ID 생성
        request_id := this.GenerateID(16)
        text := "RPC|" request_id "|" callback_name "|" ignore_response
        for p in params
            text .= "|" p

        loop 10 {
            try {
                FileAppend(text "`n", this.request_queue ,this.ENCODING)
                break
            }
            catch {
                Sleep(10)  ; 잠깐 쉬고 재시도
                ; FileAppend("331 1 1 `n", "*")
            }
        }

        ; 응답 파일 경로
        res := this.temp_path "\rpc_res_COMPLETED_" request_id ".txt"
        res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"
        ; 응답 대기
        if !ignore_response{
            loop 50 {
                if FileExist(res) {
                    ; text := FileRead(res)
                    ; if (text = ""){
                    ;     return ""
                    ; }
                    ; lines := StrSplit(result, "`n")
                    ; result := lines[1]
                    result := FileRead(res, this.ENCODING)
                    try FileDelete(res)
                    try FileDelete(res_fail)
                    return result
                }
                Sleep(100)
            }
            if FileExist(res_fail) {
                result := FileRead(res_fail , this.ENCODING)
                try FileDelete(res_fail)
                return result
            }
            return ""
        }
        return 0
        
    }

    regist(callback, callback_name) {
        this.callbacks[callback_name] := callback
        ; for cb, nm in this.callbacks{
        ;     MsgBox " " cb "!!"
        ; }
    }

    spin() {
        this.running := true
        SetTimer(() => this.check(), 100)
    }

    check() {
        ; FileAppend(A_Now, "*")
        if !FileExist(this.request_queue)
            return

        server_lock := this.AcquireServerLock(1000)
        if (!server_lock) {
            return  ; 다른 서버가 처리 중
        }
        resIgnore := false
        ; 큐 파일 독점 열기
        try {
            ; 큐 파일은 공유 모드로 열기 (클라이언트 FileAppend 허용)
            queue_file := FileOpen(this.request_queue, "rw", this.ENCODING)
            if (!queue_file) {
                return
            }

            ; 기존 처리 로직과 동일
            queue_file.Pos := 0
            text := queue_file.Read()

            ; 개행 문자 통일 처리
            text := StrReplace(text, "`r`n", "`n")  ; Windows 스타일 줄바꿈을 Unix로
            text := StrReplace(text, "`r", "`n")    ; 혹시 남은 \r도 \n으로

            lines := StrSplit(text, "`n")
            processed := false
            new_lines := []
            request_id := "", name := "", params := []
            
            for line in lines{
                line := Trim(line)
                if (line = ""){
                    ; MsgBox "Line is empty"
                    continue
                }
                if (SubStr(line, 1, 4) != "RPC|"){
                    ; MsgBox "Warn"
                    continue
                }

                if (!processed && SubStr(line, 1, 4) = "RPC|") {
                    parts := StrSplit(line, "|")
                    ; for part in parts{
                    ;     MsgBox part " !!"
                    ; }

                    if (parts.Length < 4){
                        continue
                    }
                    ; FileAppend("111 `n", "*")
                    ; MsgBox "long" " !!"
                    request_id := parts[2]
                    name := parts[3]
                    resIgnore := Number(parts[4])
                    if(!resIgnore){
                        res := this.temp_path "\rpc_res_FAIL_" request_id ".txt"
                        try FileAppend("srv_may_be_ended", res , this.ENCODING)
                    }
                        
                    ; FileAppend("222`n", "*")

                    if this.callbacks.Has(name) {
                        params := []
                        loop parts.Length - 4 {
                            val := parts[A_Index + 4]
                            params.Push(IsNumber(val) ? Number(val) : val)
                        }
                        ; MsgBox "Called, " name
                        processed := true
                        ; FileAppend("333 `n", "*")
                        continue
                    } else {
                        new_lines.Push(line)
                        ; MsgBox "Noooo"
                        continue
                    }
                }
                new_lines.Push(line)
            }

            queue_file.Pos := 0
            for l in new_lines
                queue_file.WriteLine(l)
            queue_file.Length := queue_file.Pos
            queue_file.Close()

        }
        catch {
            return
        } finally {
            ; 반드시 서버 락 해제
            this.ReleaseServerLock(server_lock)
        }
        ; for i in params{
        ;     ; MsgBox i " !!!!"
        ; }
        ; MsgBox params.Length " m"

        ; MsgBox processed
        ;  큐 정리 후 콜백
        if (processed) {
            ; FileAppend("CALLBACK EXECUTION START: " name "`n", "*")
            ; FileAppend("Params length: " params.Length "`n", "*")

            try {
                cb := this.callbacks[name]
                ; FileAppend("Callback found: " name "`n", "*")

                if params.Length = 0 {
                    ; FileAppend("Calling with 0 params`n", "*")
                    result := cb()
                }
                else if params.Length = 1 {
                    ; FileAppend("Calling with 1 param`n", "*")
                    result := cb(params[1])
                }
                else if params.Length = 2 {
                    ; FileAppend("Calling with 2 params`n", "*")
                    result := cb(params[1], params[2])
                }
                else if params.Length = 3
                    result := cb(params[1], params[2], params[3])
                else if params.Length = 4
                    result := cb(params[1], params[2], params[3], params[4])
                else if params.Length = 5
                    result := cb(params[1], params[2], params[3], params[4], params[5])
                else
                    result := cb(params[1], params[2], params[3], params[4], params[5], params[6])

                ; FileAppend("Callback executed successfully, result: " String(result) "`n", "*")
                if !resIgnore{
                    res_success := this.temp_path "\rpc_res_COMPLETED_" request_id ".txt"
                    res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"

                    try FileDelete(res_fail)
                    try FileDelete(res_success)
                    FileAppend(String(result), res_success , this.ENCODING)
                    ; FileAppend("Response file created`n", "*")
                }
            } catch as e {
                if !resIgnore{
                    ; FileAppend("CALLBACK ERROR: " e.Message "`n", "*")
                    ; FileAppend("Error at line: " e.Line "`n", "*")
                    res := this.temp_path "\rpc_res_FAIL_" request_id ".txt"
                    FileDelete(res)
                    FileAppend("ERROR: " e.Message, res , this.ENCODING)
                }
            }
        }
    }
}