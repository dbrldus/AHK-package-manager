/*
Latex Tools For Notion Math Editor
0.1.0
*/
#SingleInstance Force

global hotStringSignal := false

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
::\\d:: {
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
::\\dd:: {
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

