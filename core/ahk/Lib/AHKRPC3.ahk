#Requires AutoHotkey v2.0

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
    __New(tempPath) {
        this.callbacks := Map()
        this.running := false
        this.temp_path := tempPath
        this.request_queue := tempPath "\rpc_requests.queue"

        ; 큐 파일이 없으면 생성
        if !FileExist(this.request_queue)
            FileAppend("", this.request_queue)
    }

    AcquireExclusiveFile(path, timeout_ms := 10000) {
        start := A_TickCount
        while (A_TickCount - start < timeout_ms) {
            ; CreateFileW(path, GENERIC_READ|GENERIC_WRITE, share=0, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL)
            h := DllCall("CreateFile", "str", path, "uint", 0xC0000000, "uint", 0, "ptr", 0, "uint", 4, "uint", 0x80,
                "ptr", 0, "ptr")
            if (h != -1)  ; INVALID_HANDLE_VALUE = -1
                return FileOpen(h, "h")
            Sleep 20
        }
        throw Error("lock timeout: " path)
    }

    GenerateID(len) {
        chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        id := ""
        loop len {
            r := Random(1, StrLen(chars))
            id .= SubStr(chars, r, 1)
        }
        return id
    }

    request(callback_name, params := []) {
        request_id := this.GenerateID(16)
        text := "RPC|" request_id "|" callback_name
        for p in params
            text .= "|" p

        loop 10 {
            try {
                FileAppend(text "`n", this.request_queue)
                break
            }
            catch {
                Sleep(10)
            }
        }

        res := this.temp_path "\rpc_res_COMPLETED_" request_id ".txt"
        res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"

        loop 50 {
            if FileExist(res) {
                result := FileRead(res)
                try FileDelete(res)
                try FileDelete(res_fail)
                return result
            }
            Sleep(100)
        }
        if FileExist(res_fail) {
            result := FileRead(res_fail)
            try FileDelete(res_fail)
            return result
        }
        return ""
    }

    regist(callback, callback_name) {
        this.callbacks[callback_name] := callback
    }

    spin() {
        this.running := true
        SetTimer(() => this.check(), 100)
    }

    check() {
        if !FileExist(this.request_queue)
            return

        try queue_file := this.AcquireExclusiveFile(this.request_queue, 10000)
        catch
            return

        queue_file.Pos := 0
        text := queue_file.Read()
        lines := StrSplit(text, "`n")

        processed := false
        new_lines := []
        request_id := "", name := "", params := []

        for idx, line in lines {
            line := Trim(line)
            if (line = "")
                continue

            if (!processed && SubStr(line, 1, 4) = "RPC|") {
                parts := StrSplit(line, "|")
                if (parts.Length < 3)
                    continue

                _request_id := parts[2]
                _name := parts[3]

                res_fail_path := this.temp_path "\rpc_res_FAIL_" _request_id ".txt"
                try FileAppend("srv_may_be_ended", res_fail_path)

                if this.callbacks.Has(_name) {
                    request_id := _request_id
                    name := _name
                    params := []
                    loop parts.Length - 3 {
                        val := parts[A_Index + 3]
                        params.Push(IsNumber(val) ? Number(val) : val)
                    }
                    processed := true
                    continue
                } else {
                    new_lines.Push(line)
                    continue
                }
            }
            new_lines.Push(line)
        }

        queue_file.Pos := 0
        queue_file.Length := 0 ; 파일 내용 초기화
        for l in new_lines
            queue_file.WriteLine(l)
        queue_file.Close()

        ; ======[ 변경된 부분 시작 ]======
        ; 큐 파일 잠금을 해제한 후, 별도 스레드에서 콜백을 비동기적으로 처리
        if (processed) {
            cb := this.callbacks[name]

            ; 스레드에서 실행할 함수(클로저)를 정의합니다.
            ; 이 함수는 필요한 변수들(cb, params, request_id, this.temp_path)을 기억합니다.
            worker_func(){
                try{
                    result := cb(params*)

                    res_path := this.temp_path "\rpc_res_COMPLETED_" request_id ".txt"
                    fail_path := this.temp_path "\rpc_res_FAIL_" request_id ".txt"

                    FileDelete(res_path) ; 만약을 위해 이전 파일 삭제
                    FileAppend(String(result), res_path)
                    try FileDelete(fail_path) ; 성공 시 실패 파일 삭제
                }
                catch as e{
                    res_path := this.temp_path "\rpc_res_FAIL_" request_id ".txt"
                    FileDelete(res_path) ; 만약을 위해 이전 파일 삭제
                    FileAppend("ERROR: " e.Message, res_path)
                }
            }

            ; 정의한 함수를 새 스레드에서 실행합니다.
            Thread(worker_func)
        }
        ; ======[ 변경된 부분 끝 ]======
    }
}