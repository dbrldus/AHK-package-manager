#Requires AutoHotkey v2.0

; 하이브리드 RPC Manager - 파일 디스커버리 + TCP 통신
class RPCManager {
    __New(namespace := "default") {
        this.namespace := namespace
        this.callbacks := Map()
        this.running := false
        this.process_id := DllCall("GetCurrentProcessId")
        this.services_dir := A_Temp "\rpc_services_" namespace
        this.tcp_servers := Map()

        ; Winsock 초기화
        wsadata := Buffer(408)
        result := DllCall("ws2_32\WSAStartup", "ushort", 0x0202, "ptr", wsadata)
        if (result != 0) {
            throw Error("Winsock 초기화 실패")
        }

        DirCreate(this.services_dir)
    }

    ; 서비스 등록
    regist(callback, service_name) {
        this.callbacks[service_name] := callback

        ; 사용 가능한 포트 찾기
        port := this.FindAvailablePort(9000, 9999)
        if (!port) {
            throw Error("사용 가능한 포트를 찾을 수 없습니다")
        }

        ; TCP 서버 시작
        server := this.StartTCPServer(port, service_name)
        if (!server) {
            throw Error("TCP 서버 시작 실패: " service_name)
        }

        this.tcp_servers[service_name] := { port: port, server: server }

        ; 서비스 파일 등록 (디스커버리용)
        service_file := this.services_dir "\" service_name "_proc" this.process_id "_port" port ".service"
        try {
            FileAppend(this.process_id "|" port "|" A_Now, service_file)
        } catch {
            throw Error("서비스 등록 실패: " service_name)
        }

        return true
    }

    ; 서비스 요청 - TCP 기반으로 수정
    request(service_name, params := [], timeout_ms := 5000) {
        ; 서비스 디스커버리
        servers := this.DiscoverService(service_name)
        if (servers.Length = 0) {
            return "ERROR: 서비스를 찾을 수 없음 - " service_name
        }

        ; 랜덤 서버 선택 (로드 밸런싱)
        server := servers[Random(1, servers.Length)]

        ; TCP 연결 및 요청
        return this.SendTCPRequest(server.host, server.port, service_name, params, timeout_ms)
    }

    ; 서비스 디스커버리 (파일 스캔)
    DiscoverService(service_name) {
        servers := []
        pattern := service_name "_proc*_port*.service"

        loop files, this.services_dir "\" pattern {
            try {
                content := FileRead(A_LoopFileFullPath)
                parts := StrSplit(content, "|")
                if (parts.Length >= 2) {
                    proc_id := parts[1]
                    port := parts[2]

                    if (ProcessExist(proc_id)) {
                        servers.Push({
                            host: "127.0.0.1",
                            port: port,
                            process_id: proc_id,
                            file: A_LoopFileFullPath
                        })
                    } else {
                        FileDelete(A_LoopFileFullPath)
                    }
                }
            }
        }

        return servers
    }

    ; 사용 가능한 포트 찾기
    FindAvailablePort(start_port, end_port) {
        loop end_port - start_port + 1 {
            port := start_port + A_Index - 1
            if (this.IsPortAvailable(port)) {
                return port
            }
        }
        return 0
    }

    ; 포트 사용 가능 여부 확인
    IsPortAvailable(port) {
        try {
            test_socket := DllCall("ws2_32\socket", "int", 2, "int", 1, "int", 6, "ptr")
            if (test_socket = -1) {
                return false
            }

            addr := this.CreateSockAddr("127.0.0.1", port)
            bind_result := DllCall("ws2_32\bind", "ptr", test_socket, "ptr", addr, "int", 16)
            DllCall("ws2_32\closesocket", "ptr", test_socket)

            return (bind_result = 0)
        } catch {
            return false
        }
    }

    ; TCP 서버 시작
    StartTCPServer(port, service_name) {
        try {
            server_socket := DllCall("ws2_32\socket", "int", 2, "int", 1, "int", 6, "ptr")
            if (server_socket = -1) {
                return false
            }

            addr := this.CreateSockAddr("127.0.0.1", port)
            if (DllCall("ws2_32\bind", "ptr", server_socket, "ptr", addr, "int", 16) != 0) {
                DllCall("ws2_32\closesocket", "ptr", server_socket)
                return false
            }

            if (DllCall("ws2_32\listen", "ptr", server_socket, "int", 10) != 0) {
                DllCall("ws2_32\closesocket", "ptr", server_socket)
                return false
            }

            return server_socket
        } catch {
            return false
        }
    }

    ; TCP 요청 전송
    SendTCPRequest(host, port, service_name, params, timeout_ms) {
        try {
            client_socket := DllCall("ws2_32\socket", "int", 2, "int", 1, "int", 6, "ptr")
            if (client_socket = -1) {
                return "ERROR: 소켓 생성 실패"
            }

            ; 타임아웃 설정
            timeout_val := Buffer(4)
            NumPut("uint", timeout_ms, timeout_val, 0)
            DllCall("ws2_32\setsockopt", "ptr", client_socket, "int", 0xFFFF, "int", 0x1005, "ptr", timeout_val, "int",
                4)

            addr := this.CreateSockAddr(host, port)
            if (DllCall("ws2_32\connect", "ptr", client_socket, "ptr", addr, "int", 16) != 0) {
                DllCall("ws2_32\closesocket", "ptr", client_socket)
                return "ERROR: 서버 연결 실패 " host ":" port
            }

            ; 요청 데이터 구성
            request_id := this.GenerateID(16)
            request_data := "REQ|" request_id "|" service_name
            for p in params {
                request_data .= "|" p
            }

            ; 데이터 전송
            sent := DllCall("ws2_32\send", "ptr", client_socket, "astr", request_data, "int", StrLen(request_data),
            "int", 0)
            if (sent <= 0) {
                DllCall("ws2_32\closesocket", "ptr", client_socket)
                return "ERROR: 전송 실패"
            }

            ; 응답 수신
            response := this.ReceiveTCPResponse(client_socket, timeout_ms)
            DllCall("ws2_32\closesocket", "ptr", client_socket)

            return response
        } catch as e {
            return "ERROR: " e.Message
        }
    }

    ; TCP 응답 수신
    ReceiveTCPResponse(socket, timeout_ms) {
        recv_data := Buffer(4096)

        ; 수신 타임아웃 설정
        timeout_val := Buffer(4)
        NumPut("uint", timeout_ms, timeout_val, 0)
        DllCall("ws2_32\setsockopt", "ptr", socket, "int", 0xFFFF, "int", 0x1006, "ptr", timeout_val, "int", 4)

        received := DllCall("ws2_32\recv", "ptr", socket, "ptr", recv_data, "int", 4096, "int", 0)
        if (received > 0) {
            return StrGet(recv_data, received, "UTF-8")
        }

        return "TIMEOUT"
    }

    ; 서버 시작
    spin() {
        this.running := true

        for service_name, server_info in this.tcp_servers {
            bound_func := ObjBindMethod(this, "AcceptConnections", service_name)
            SetTimer(bound_func, 50)
        }

        cleanup_func := ObjBindMethod(this, "CleanupDeadServices")
        SetTimer(cleanup_func, 10000)
    }

    ; 연결 수락 및 처리
    AcceptConnections(service_name) {
        if (!this.tcp_servers.Has(service_name)) {
            return
        }

        server_socket := this.tcp_servers[service_name].server

        client_socket := DllCall("ws2_32\accept", "ptr", server_socket, "ptr", 0, "ptr", 0, "ptr")
        if (client_socket != -1) {
            response := this.ProcessTCPRequest(client_socket, service_name)

            if (response != "") {
                DllCall("ws2_32\send", "ptr", client_socket, "astr", response, "int", StrLen(response), "int", 0)
            }

            DllCall("ws2_32\closesocket", "ptr", client_socket)
        }
    }

    ; TCP 요청 처리 - 변수명 수정
    ProcessTCPRequest(client_socket, service_name) {
        try {
            recv_data := Buffer(4096)
            received := DllCall("ws2_32\recv", "ptr", client_socket, "ptr", recv_data, "int", 4096, "int", 0)

            if (received <= 0) {
                return "ERROR: 데이터 수신 실패"
            }

            request_data := StrGet(recv_data, received, "UTF-8")  ; 변수명 수정
            parts := StrSplit(request_data, "|")

            if (parts.Length < 3 || parts[1] != "REQ") {
                return "ERROR: 잘못된 요청 형식"
            }

            request_id := parts[2]
            received_service := parts[3]
            params := []

            loop parts.Length - 3 {
                val := parts[A_Index + 3]
                params.Push(IsNumber(val) ? Number(val) : val)
            }

            if (!this.callbacks.Has(service_name)) {
                return "ERROR: 서비스가 등록되지 않음 - " service_name
            }

            cb := this.callbacks[service_name]
            if (params.Length = 0) {
                result := cb()
            } else if (params.Length = 1) {
                result := cb(params[1])
            } else if (params.Length = 2) {
                result := cb(params[1], params[2])
            } else {
                result := cb(params*)
            }

            return String(result)
        } catch as e {
            return "ERROR: " e.Message
        }
    }

    ; 죽은 서비스 정리
    CleanupDeadServices() {
        loop files, this.services_dir "\*.service" {
            try {
                content := FileRead(A_LoopFileFullPath)
                parts := StrSplit(content, "|")
                if (parts.Length >= 1) {
                    proc_id := parts[1]
                    if (!ProcessExist(proc_id)) {
                        FileDelete(A_LoopFileFullPath)
                    }
                }
            }
        }
    }

    ; 헬퍼 함수들
    GenerateID(len) {
        chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        id := ""
        loop len {
            r := Random(1, StrLen(chars))
            id .= SubStr(chars, r, 1)
        }
        return id
    }

    CreateSockAddr(ip, port) {
        addr := Buffer(16, 0)
        NumPut("ushort", 2, addr, 0)
        NumPut("ushort", this.htons(port), addr, 2)
        NumPut("uint", 0x0100007F, addr, 4)
        return addr
    }

    htons(port) {
        return ((port & 0xFF) << 8) | ((port >> 8) & 0xFF)
    }
}