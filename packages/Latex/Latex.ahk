/*
Latex Tools For Notion Math Editor
0.1.0
*/
#SingleInstance Force

::\mb:: {
    SendText("/mat")
    SendInput("h{Enter}")
}
::\mi:: {
    SendInput("^+e")
    Sleep(50)
    SendText("aaa")
    SendInput("{Enter}")
}
::\ma:: {
    SendText("\begin{align*}")
    Send("+{Enter}")
    Send("+{Enter}")
    SendText("\end{align*}")
    Send("{Up}")
}

::\dp:: {
    SendText("\displaystyle")
}

::\lr:: {
    SendText("\left(  \right)")
    Send("{Left 7}")
}
::\fr:: {
    SendText("\frac{}{}")
    Send("{Left 3}")
}

::\sq:: {
    SendText("\sqrt{}")
    Send("{Left}")
}

::\mat:: {
    SendText("\begin{bmatrix}")
    Send("+{Enter}")
    Send("+{Enter}")
    SendText("\end{bmatrix}")
    Send("{Up}")
}

::\lim:: {
    SendText("\lim_{ \to }")
    Send("{Left 5}")
}

:*?:\diff::
{
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\frac{d}{d" ch "}")
}

:*?:\pdiff::
{
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\frac{\partial}{\partial " ch "}")
}

::\int:: {
    SendText("\int_{}^{}")
    Send("{Left 4}")
}
::\inti:: {
    SendText("\int_{-\infty}^{\infty}")
}

::\h:: {
    SendText("\hat{}")
    SendInput("{Left}")
}
::\bb:: {
    SendText("\mathbb{}")
    SendInput("{Left}")
}

::\cal::{
    SendText("\mathcal{}")
    SendInput("{Left}")
}

;Greek Alphabet
::\a:: {
    SendText("\alpha")
}
::\b:: {
    SendText("\beta")
}
::\d::{
    SendText("\delta")
}
::\ld:: {
    SendText("\Delta")
}
::\t:: {
    SendText("\theta")
}
::\l:: {
    SendText("\lambda")
}
::\w:: {
    SendText("\omega")
}
::\x:: {
    SendText("\xi")
}
::\z:: {
    SendText("\zeta")
}

; Direct input
::\da:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\alpha")
    SendInput("{Enter}")
}
::\db:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\beta")
    SendInput("{Enter}")
}
::\dd:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\delta")
    SendInput("{Enter}")
}
::\dld:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\Delta")
    SendInput("{Enter}")
}
::\dt:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\theta")
    SendInput("{Enter}")
}
::\dl:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\lambda")
    SendInput("{Enter}")
}
::\dw:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\omega")
    SendInput("{Enter}")
}
::\dx:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\xi")
    SendInput("{Enter}")
}
::\dz:: {
    SendInput("^+e")
    Sleep(50)
    SendText("\zeta")
    SendInput("{Enter}")
}
::\dcal::{
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendInput("^+e")
    Sleep(50)
    SendText("\mathcal{ " ch "}")
    SendInput("{Enter}")
    ih.Stop()
}

::\din:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendInput("^+e")       ; 수식 편집기 열기
    Sleep(50)
    SendText(ch)           ; 입력 텍스트 삽입
    ; 수식 닫기
    SendInput("{Enter}")
    ih.Stop()
}

::\p:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("^{" ch "}")
    ih.Stop()
}

+Space::{
    SendInput("{Right}")
}

:*?:^:: {
    SendText("^{}")
    SendInput("{Left}")
}

:*?:_:: {
    SendText("_{}")
    Send("{Left}")
}

::\do:: {
    SendText("\dot{}")
    Send("{Left}")
}
:*?:\dot::{
    SendText("\dot{}")
    Send("{Left}")
}

;커서 이동
; 왼쪽 가장 가까운 중괄호까지 커서 이동
<!,:: {
    OriginalClipboard := A_Clipboard
    A_Clipboard := ""
    SendInput("+^{Home}")
    SendInput("^c")
    if !ClipWait(0.5) { ; 0.5초 안에 복사되지 않으면 중단
        A_Clipboard := OriginalClipboard
        return
    }
    CopiedText := A_Clipboard
    SendInput("{Right}")

    CleanedText := StrReplace(CopiedText, "`r`n", "`n")
    Position := StrLen(CleanedText) - InStr(CleanedText, "}", , , -1)
    if (Position >= 0) {
        Send("{Left " Position + 1 "}")
    }
    A_Clipboard := OriginalClipboard
    return
}

; 오른쪽 가장 가까운 중괄호까지 커서 이동
<!.:: {
    OriginalClipboard := A_Clipboard
    A_Clipboard := ""
    SendInput("+^{End}")
    SendInput("^c")
    if !ClipWait(0.5) { ; 0.5초 안에 복사되지 않으면 중단
        A_Clipboard := OriginalClipboard
        return
    }
    CopiedText := A_Clipboard
    SendInput("{Left}")

    CleanedText := StrReplace(CopiedText, "`r`n", "`n")
    Position := 0
    if (SubStr(CleanedText, 1, 1) == "}") {
        Position := InStr("A" SubStr(CleanedText, 2), "}")
    }
    else {
        Position := InStr(CleanedText, "}")
    }

    if (Position > 0) {
        Count := Position
        Send("{Right " Count "}")
        Send("{Left}")
    }
    else {
        Send("{End}")
    }
    A_Clipboard := OriginalClipboard
    return
}

::\utt::{
    Send("^+e")
    Sleep(50)
    SendText("^{\text{}}")
    SendInput("{Left 2}")
}

;#region number alphabet

::\na:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\alpha")
    SendText("_{" ch "}")
}
::\nb:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\beta")
    SendText("_{" ch "}")
}
::\nd:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\delta")
    SendText("_{" ch "}")
}
::\nld:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\Delta")
    SendText("_{" ch "}")
}
::\nt:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\theta")
    SendText("_{" ch "}")
}
::\nl:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\lambda")
    SendText("_{" ch "}")
}
::\nw:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\omega")
    SendText("_{" ch "}")
}
::\nx:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\xi")
    SendText("_{" ch "}")
}
::\nz:: {
    ih := InputHook("V", "{Space}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch) + 1
    Send("{Backspace " len "}")
    SendText("\zeta")
    SendText("_{" ch "}")
}

;#endregion

::\skew::{
    SendText("\begin{bmatrix}")
    SendInput("+{Enter}")
    SendInput("+{Enter}")
    SendText("\end{bmatrix}")
    Send("{Up}")
    input_queue := [] 
    try{
        loop 3{
            ih := InputHook("V", "{Space}")
            ih.Start()
            ih.Wait()
            ch := ih.Input
            input_queue.Push(String(ch))
            len := StrLen(ch) + 1
            Send("{Backspace " len "}")
        }
        SendText("0 & -" input_queue[3] " & " input_queue[2] " \\")
        SendInput("+{Enter}")
        SendText(input_queue[3] " & 0 & -" input_queue[1] " \\")
        SendInput("+{Enter}")
        SendText( "-" input_queue[2] " & " input_queue[1] " & 0 \\")
        SendInput("{Down 2}")
    }
}