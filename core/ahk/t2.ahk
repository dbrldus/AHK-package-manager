; RPC 서버 예제
#Requires AutoHotkey v2.0
#Include <AHKRPC3>  ; 위의 최종 코드를 AHKRPC3.ahk로 저장

; RPC 매니저 생성
rpc := RPCManager("testapp")

; 콜백 함수들 정의
ping(message) {
    MsgBox "ping 호출됨: " message
    return "pong " message
}

add(a, b) {
    result := Number(a) + Number(b)
    MsgBox "add(" a ", " b ") = " result
    return result
}

echo(text) {
    MsgBox "echo 호출됨: " text
    return "Echo: " text
}

getCurrentTime() {
    current_time := A_Now
    MsgBox "getCurrentTime 호출됨"
    return current_time
}

; 서비스 등록
try {
    rpc.regist(ping, "ping")
    MsgBox "ping 서비스 등록 완료"

    rpc.regist(add, "add")
    MsgBox "add 서비스 등록 완료"

    rpc.regist(echo, "echo")
    MsgBox "echo 서비스 등록 완료"

    rpc.regist(getCurrentTime, "time")
    MsgBox "time 서비스 등록 완료"

} catch as e {
    MsgBox "서비스 등록 실패: " e.Message
    ExitApp
}

; 서버 시작
MsgBox "RPC 서버를 시작합니다..."
rpc.spin()

; 서버가 실행 중임을 표시
; MsgBox "RPC 서버가 실행 중입니다.`n등록된 서비스:`n- ping`n- add`n- echo`n- time`n`n이 창을 닫으면 서버가 종료됩니다."