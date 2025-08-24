::\t::{
    sendText("\theta")
}
::\f::{
    sendText("\frac{}{}")
    send("{Left}{Left}{Left}")
}
::\a::{
    sendText("\alpha")
}
::\b::{
    sendText("\beta")
}
::\c::{
    sendText("\gamma")
}
::\d::{
    sendText("\delta")
}
::\D::{
    sendText("\Delta")
}
`::{
    sendInput("^+e")
}
::\w::{
    sendText("\omega")
}
::\h::{
    sendText("\hat{}")
    Send("{Left}")
}
::\bmat::{
    sendText("\begin{bmatrix}")
    Send("+{Enter}")
    Send("+{Enter}")
    sendText("\end{bmatrix}")
    Send("{Up}")
}
::\sq::{
    sendText("\sqrt{}")
    send("{Left}")
}


F1::{
    OriginalClipboard := A_Clipboard
    A_Clipboard := ""
    SendInput("+^{End}")
    SendInput("^c")
    ClipWait("0.3")

    CopiedText := A_Clipboard
    Position := InStr(CopiedText, "{}")
    SendInput("{Left}")
    if (Position > 0) {
        Count := Position
        Send("{Right " Count "}")
    }
    A_Clipboard := OriginalClipboard
    Return
}

^b::{
    SendMode "Input"
    SetKeyDelay -1

    ; 1) 단어 처음으로 이동 (반드시 브레이스!)
    Send "^{Left}"
    KeyWait "Ctrl"

    ; 2) 직전 8글자 확인용 클립보드 백업/초기화
    cb := ClipboardAll()
    A_Clipboard := ""

    ; 커서 왼쪽 8글자 선택 → 복사
    Send "+{Right 8}"
    Sleep 20
    Send "^c"
    ClipWait 0.2
    prev8 := A_Clipboard

    Send "{Left}"

    if (prev8 = "\mathbf{") {
        ; 3A) 앞의 "\mathbf{" 삭제
        Send Format("{{Del {}}}", StrLen(prev8))

        ; 단어 끝으로 이동
        Send "^{Right}"
        KeyWait "Ctrl"

        ; 다음 글자가 '}'면 삭제
        A_Clipboard := ""
        Send "+{Right}"     ; 한 글자 선택
        Sleep 10
        Send "^c"
        ClipWait 0.2
        next1 := A_Clipboard
        Send "{Left}"
        if (next1 = "}")
            Send "{Del}"
    } else {
        ; 3B) 앞에 "\mathbf{" 삽입 → 단어 끝으로 → '}' 삽입
        SendText "\mathbf{"
        Send "^{Right}"
        KeyWait "Ctrl"
        SendText "}"
    }

    ; 클립보드 복원
    Clipboard := cb
}