; RPC 클라이언트 예제
#Requires AutoHotkey v2.0
#Include <AHKRPC3>  ; 위의 최종 코드를 AHKRPC3.ahk로 저장

; RPC 매니저 생성 (같은 네임스페이스 사용)
client := RPCManager("testapp")

MsgBox "RPC 클라이언트 테스트를 시작합니다.`n서버가 실행 중인지 확인하세요."

; 1. ping 서비스 테스트
MsgBox "1. ping 서비스 테스트"
try {
    result := client.request("ping", ["Hello World!"], 3000)
    MsgBox "ping 결과: " result
} catch as e {
    MsgBox "ping 오류: " e.Message
}

; 2. add 서비스 테스트
MsgBox "2. add 서비스 테스트"
try {
    result := client.request("add", [15, 25], 3000)
    MsgBox "add(15, 25) 결과: " result
} catch as e {
    MsgBox "add 오류: " e.Message
}

; 3. echo 서비스 테스트
MsgBox "3. echo 서비스 테스트"
try {
    result := client.request("echo", ["안녕하세요 RPC!"], 3000)
    MsgBox "echo 결과: " result
} catch as e {
    MsgBox "echo 오류: " e.Message
}

; 4. time 서비스 테스트 (파라미터 없음)
MsgBox "4. time 서비스 테스트"
try {
    result := client.request("time", [], 3000)
    MsgBox "현재 시간: " result
} catch as e {
    MsgBox "time 오류: " e.Message
}

; 5. 존재하지 않는 서비스 테스트
MsgBox "5. 존재하지 않는 서비스 테스트"
try {
    result := client.request("nonexistent", ["test"], 3000)
    MsgBox "nonexistent 결과: " result
} catch as e {
    MsgBox "nonexistent 오류: " e.Message
}

; 6. 연속 요청 테스트
MsgBox "6. 연속 요청 테스트"
loop 3 {
    try {
        result := client.request("ping", ["요청 #" A_Index], 3000)
        MsgBox "연속 요청 " A_Index " 결과: " result
    } catch as e {
        MsgBox "연속 요청 " A_Index " 오류: " e.Message
    }
}

MsgBox "RPC 클라이언트 테스트 완료!"