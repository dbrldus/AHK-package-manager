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

        ; Map으로 O(1) 조회 - ID를 키로, 타임스탬프를 값으로
        this.duplicate_window := 2  ; 2초

        fileAutoGen(this.request_queue)
    }

    AcquireServerLock(timeout_ms := 1000) {
        lock_file := this.temp_path "\rpc_server.lock"
        start_time := A_TickCount

        while (A_TickCount - start_time < timeout_ms) {
            if (!FileExist(lock_file)) {
                try {
                    FileAppend(DllCall("GetCurrentProcessId") "|" A_Now, lock_file)
                    return lock_file
                }
            } else {
                ; 기존 락 파일 확인 및 강제 해제
                try {
                    lock_content := FileRead(lock_file)
                    parts := StrSplit(lock_content, "|")
                    if (parts.Length >= 2) {
                        lock_pid := parts[1]
                        lock_time := parts[2]

                        ; 5분 초과 또는 프로세스 죽음 확인
                        time_diff := this.GetTimeDifferenceSeconds(lock_time, A_Now)
                        if (time_diff > 1 || !ProcessExist(lock_pid)) {
                            FileDelete(lock_file)
                            continue
                        }
                    }
                } catch {
                    ; 손상된 락 파일은 삭제
                    FileDelete(lock_file)
                    continue
                }
            }
            Sleep(20)
        }
        return false
    }

    ReleaseServerLock(lock_file) {
        if (lock_file && FileExist(lock_file)) {
            FileDelete(lock_file)
        }
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

    request(callback_name, params := [], ignore_response := false) {
        request_id := this.GenerateID(16)
        timestamp := A_Now  ; YYYYMMDDHHMISS 형식

        ; 새로운 형식: RPC|ID|NAME|IGNORE|TIMESTAMP|PARAMS...
        text := "RPC|" request_id "|" callback_name "|" ignore_response "|" timestamp
        for p in params
            text .= "|" p

        ; 요청 전송 시도
        loop 10 {
            try {
                FileAppend(text "`n", this.request_queue, this.ENCODING)
                break
            }
            catch {
                Sleep(10)
            }
        }

        ; 응답 대기
        if !ignore_response {
            res := this.temp_path "\rpc_res_COMPLETED_" request_id ".txt"
            res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"

            loop 50 {
                if FileExist(res) {
                    result := FileRead(res, this.ENCODING)
                    try FileDelete(res)
                    try FileDelete(res_fail)
                    return result
                }
                Sleep(100)
            }

            if FileExist(res_fail) {
                result := FileRead(res_fail, this.ENCODING)
                try FileDelete(res_fail)
                return 1
            }
            return 1
        }
        return 0
    }

    regist(callback, callback_name) {
        this.callbacks[callback_name] := callback
    }

    spin() {
        this.running := true
        SetTimer(() => this.check(), 100)
    }


    CleanupProcessedRequests() {
        processed_file := this.temp_path "\processed_requests.txt"
        if (!FileExist(processed_file)){
            return
        } 
        try {
            ; 파일 크기 확인 - 너무 크면 정리
            file_size := FileGetSize( processed_file)
            if (file_size < 10240) {  ; 10KB 미만이면 건너뛰기
                return
            }

            content := FileRead(processed_file)
            lines := StrSplit(content, "`n")
            new_lines := []
            current_time := A_Now
            removed_count := 0

            for line in lines {
                if (line = ""){
                    continue
                }
                parts := StrSplit(line, "|")
                if (parts.Length >= 2) {
                    time_diff := this.GetTimeDifferenceSeconds(parts[2], current_time)
                    if (time_diff <= this.duplicate_window) {
                        new_lines.Push(line)
                    } else {
                        removed_count++
                    }
                }
            }

            ; 정리할 게 있으면 파일 업데이트
            if (removed_count > 0) {
                FileDelete(processed_file)
                for line in new_lines {
                    FileAppend(line "`n", processed_file)
                }
            }
        }
    }

    ; 중복 요청 검사 - O(1)
    IsDuplicateRequest(request_id, timestamp) {
        processed_file := this.temp_path "\processed_requests.txt"

        if (!FileExist(processed_file)) {
            return false
        }

        try {
            content := FileRead(processed_file)
            lines := StrSplit(content, "`n")

            for line in lines {
                if (line = ""){
                    continue
                }
                parts := StrSplit(line, "|")
                if (parts.Length >= 2 && parts[1] = request_id) {
                    time_diff := this.GetTimeDifferenceSeconds(parts[2], timestamp)
                    if (time_diff <= this.duplicate_window) {
                        return true
                    }
                }
            }
        }
        return false
    }

    RecordProcessedRequest(request_id, timestamp) {
        processed_file := this.temp_path "\processed_requests.txt"
        try {
            FileAppend(request_id "|" timestamp "`n", processed_file)
        }
    }

    ; 시간 차이 계산 (초 단위)
    GetTimeDifferenceSeconds(time1, time2) {
        ; YYYYMMDDHHMISS 형식을 초로 변환해서 차이 계산
        t1 := DateDiff(time1, "19700101000000", "Seconds")
        t2 := DateDiff(time2, "19700101000000", "Seconds")
        return Abs(t2 - t1)
    }

    check() {
        
        if !FileExist(this.request_queue)
            return

        server_lock := this.AcquireServerLock(1000)
        if (!server_lock) {
            return
        }
        static last_cleanup := 0
        current_time := A_TickCount
        if (current_time - last_cleanup > 30000) {
            this.CleanupProcessedRequests()
            last_cleanup := current_time
        }
        try {
            queue_file := FileOpen(this.request_queue, "rw", this.ENCODING)
            if (!queue_file) {
                return
            }

            queue_file.Pos := 0
            text := queue_file.Read()

            text := StrReplace(text, "`r`n", "`n")
            text := StrReplace(text, "`r", "`n")

            lines := StrSplit(text, "`n")
            new_lines := []

            request_to_process := ""
            callback_name := ""
            callback_params := []
            ignore_response := false

            for line in lines {
                line := Trim(line)
                if (line = "") {
                    continue  ; 빈 줄은 무시
                }
                if (SubStr(line, 1, 4) != "RPC|") {
                    ; 더미 문자열은 로그 후 제거 (보존하지 않음)
                    ; FileAppend("Invalid queue line removed: " line "`n", A_ScriptDir "\queue_cleanup.log")
                    continue
                }

                parts := StrSplit(line, "|")
                if (parts.Length < 5) {  ; 최소 RPC|ID|NAME|IGNORE|TIMESTAMP
                    continue
                }

                request_id := parts[2]
                name := parts[3]
                ignore_resp := Number(parts[4])
                timestamp := parts[5]

                ; 중복 요청 검사
                if (this.IsDuplicateRequest(request_id, timestamp)) {
                    ; 중복 발견 - 큐에서 제거하고 무시
                    continue
                }

                ; 유효한 콜백이 있고 아직 처리할 요청이 없는 경우
                if (request_to_process = "" && this.callbacks.Has(name)) {
                    request_to_process := request_id
                    callback_name := name
                    ignore_response := ignore_resp

                    ; 파라미터 추출 (timestamp 이후)
                    callback_params := []
                    loop parts.Length - 5 {
                        val := parts[A_Index + 5]
                        callback_params.Push(IsNumber(val) ? Number(val) : val)
                    }

                    ; 최근 요청 Map에 추가 - O(1)
                    this.RecordProcessedRequest(request_id, timestamp)

                    ; FAIL 응답 파일 미리 생성
                    if (!ignore_response) {
                        res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"
                        try FileAppend("1", res_fail, this.ENCODING)
                    }

                    ; 큐에서 제거
                    continue
                }

                ; 처리하지 않는 요청들은 큐에 보존
                new_lines.Push(line)
            }

            ; 큐 파일 업데이트
            queue_file.Pos := 0
            if (new_lines.Length > 0) {
                for line in new_lines {
                    queue_file.WriteLine(line)
                }
            }
            queue_file.Length := queue_file.Pos
            queue_file.Close()

        } catch {
            return
        } finally {
            this.ReleaseServerLock(server_lock)
        }

        ; 콜백 실행
        if (request_to_process != "") {
            this.ExecuteCallback(request_to_process, callback_name, callback_params, ignore_response)
        }
    }

    ExecuteCallback(request_id, name, params, ignore_response) {
        try {
            cb := this.callbacks[name]

            if (params.Length = 0) {
                result := cb()
            } else if (params.Length = 1) {
                result := cb(params[1])
            } else if (params.Length = 2) {
                result := cb(params[1], params[2])
            } else if (params.Length = 3) {
                result := cb(params[1], params[2], params[3])
            } else if (params.Length = 4) {
                result := cb(params[1], params[2], params[3], params[4])
            } else if (params.Length = 5) {
                result := cb(params[1], params[2], params[3], params[4], params[5])
            } else {
                result := cb(params[1], params[2], params[3], params[4], params[5], params[6])
            }

            if (!ignore_response) {
                res_success := this.temp_path "\rpc_res_COMPLETED_" request_id ".txt"
                res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"

                try FileDelete(res_fail)
                try FileDelete(res_success)
                FileAppend(String(result), res_success, this.ENCODING)
            }

        } catch as e {
            if (!ignore_response) {
                res_fail := this.temp_path "\rpc_res_FAIL_" request_id ".txt"
                try FileDelete(res_fail)
                FileAppend("ERROR: " e.Message, res_fail, this.ENCODING)
            }
        }
    }
}
