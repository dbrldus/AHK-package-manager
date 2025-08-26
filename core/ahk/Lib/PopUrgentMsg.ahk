#Requires AutoHotkey v2.0

; 명령줄 인자 받기
args := A_Args

if (args.Length >= 2) {
    title := args[1]
    content := args[2]
    MsgBox(content, title, "OK")
} else {
    MsgBox("Insufficient arguments.", "Err", "OK")
}