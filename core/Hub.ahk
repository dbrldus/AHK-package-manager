#Requires AutoHotkey v2
#SingleInstance Force

; 라이브러리 경로에 JSON.ahk, HubRPC.ahk가 있어야 함
#Include <JSON>
#Include <HubRPC>

; RPC 수신 시작
HubRPC.Start()
HubRPC.AllowAll(false)  ; 등록된 함수만 호출 허용 (권장)

; 테스트용 함수 등록
Add(a, b) {
    return a + b
}
HubRPC.Register("Add", Add)

class LatexPkg {
    static ToggleBold(text := "") {
        return text ? "\mathbf{" text "}" : "\mathbf{}"
    }
}
HubRPC.Register("Latex.ToggleBold", LatexPkg.ToggleBold)

; 살아있게 유지

TrayTip "Hub", "RPC ready"
return
