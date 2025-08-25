; PyRPC.ahk - Ultra simple RPC
    class RPCManager {
        __New(tempPath) {
            this.callbacks := Map()
            this.running := false
            this.temp_path := tempPath
        }

        regist(callback, callback_name) {
            this.callbacks[callback_name] := callback
        }

        request(callback_name, params := []) {
            svc := callback_name
            req := this.temp_path "\rpc_req_" svc ".txt"   ; ← 변경
            res := this.temp_path "\rpc_res_" svc ".txt"   ; ← 변경
            try FileDelete(res)

            text := "PY|" callback_name
            for p in params
                text .= "|" p

            FileAppend(text, req)

            loop 50 {
                if FileExist(res) {
                    result := FileRead(res)
                    try FileDelete(res)
                    try FileDelete(req)
                    return result
                }
                Sleep(100)
            }
            try FileDelete(req)
            return ""
        }

        spin() {
            this.running := true
            SetTimer(() => this.check(), 100)
        }

        check() {
            ; 1) 서비스명 기반 요청 먼저 처리
            loop files, this.temp_path "\rpc_req_*.txt" {
                req := A_LoopFileFullPath
                res := StrReplace(req, "rpc_req_", "rpc_res_")  ; 확장자 유지
                try text := FileRead(req)
                catch as c
                    if !InStr(text, "AHK|")
                        continue

                try FileDelete(req)

                parts := StrSplit(text, "|")
                if parts.Length < 2
                    continue
                name := parts[2]

                if !this.callbacks.Has(name) {
                    FileAppend("ERROR", res)
                    continue
                }

                params := []
                loop parts.Length - 2 {
                    val := parts[A_Index + 2]
                    params.Push(IsNumber(val) ? Number(val) : val)
                }

                try {
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
                        result := this.callbacks[name](params[1], params[2], params[3], params[4], params[5], params[6]
                        )

                    FileAppend(String(result), res)
                } catch {
                    FileAppend("ERROR", res)
                }
                return  ; 한 번에 하나만 처리(기존 타이머 리듬 유지)
            }
        }
    }