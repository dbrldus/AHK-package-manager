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

    GenerateID() {
        ; 랜덤 ID 생성 (12자리)
        chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        id := ""
        loop 12 {
            r := Random(1, StrLen(chars))  ; 1 ~ 길이 사이 정수
            id .= SubStr(chars, r, 1)      ; r번째 글자 1개 추출
        }
        return id
    }

    request(callback_name, params := []) {
        ; 고유 ID 생성
        request_id := this.GenerateID()

        ; 요청 텍스트 생성
        text := "RPC|" request_id "|" callback_name
        for p in params
            text .= "|" p

        ; 큐 파일에 추가
        loop 10 {
            try {
                FileAppend(text "`n", this.request_queue)
                break
            }
            catch {
                Sleep(10)  ; 잠깐 쉬고 재시도
            }
        }

        ; 응답 파일 경로
        res := this.temp_path "\rpc_res_" request_id ".txt"

        ; 응답 대기
        loop 50 {
            if FileExist(res) {
                result := FileRead(res)
                try FileDelete(res)
                return result
            }
            Sleep(100)
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

        ; 큐 파일 읽기
        try text := FileRead(this.request_queue)
        catch
            return

        lines := StrSplit(text, "`n")
        
        processed := false
        remaining := []

        for line in lines {
            line := Trim(line)
            if line = ""
                continue
            if !processed && SubStr(line, 1, 4) = "RPC|" {
                ; MsgBox line
                parts := StrSplit(line, "|")
                if parts.Length < 3{
                    continue
                }
                request_id := parts[2]
                name := parts[3]
                res := this.temp_path "\rpc_res_" request_id ".txt"
                ; MsgBox "res gen!" request_id
                if !this.callbacks.Has(name) {
                    remaining.Push(line)
                    continue
                }
                params := []
                loop parts.Length - 3 {
                    val := parts[A_Index + 3]
                    params.Push(IsNumber(val) ? Number(val) : val)
                }
                try { ; 콜백 실행
                    if params.Length = 0
                        result := this.callbacks[name]()
                else if params.Length = 1
                    result := this.callbacks[name](params[1])
                else if params.Length = 2
                    result := this.callbacks[name](params[1], params[2])
                else if params.Length = 3
                    result := this.callbacks[name](params[1], params[2], params[3])
                else if params.Length = 4
                    result := this.callbacks[name](params[1], params[2], params[3], params[4])
                else if params.Length = 5
                    result := this.callbacks[name](params[1], params[2], params[3], params[4], params[5])
                else
                    result := this.callbacks[name](params[1], params[2], params[3], params[4], params[5], params[6])
                
                FileAppend(String(result), res)
            } catch {
                FileAppend("ERROR", res)
            }
            processed := true
            }
        }
        ; 처리한 줄 제거하고 큐 파일 업데이트
        if processed {
            try {
                f := FileOpen(file, "w", "UTF-8")  ; "w" = 덮어쓰기
                for line in lines
                    f.WriteLine(line)
            }
        }
    }
}