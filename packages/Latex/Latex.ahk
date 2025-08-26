::\mb::{
    SendText("/mat")
    SendInput("h{Enter}")
}
::\mi::{
    SendInput("^+e")
}
::\ma::{
    SendText("\begin{align*}")
    Send("+{Enter}")
    Send("+{Enter}")
    SendText("\end{align*}")
    Send("{Up}")
}

::\dp::{
    SendText("\displaystyle")
}

::\lr::{
    SendText("\left(  \right)")
    Send("{Left 7}")
}
::\fr::{
    SendText("\frac{}{}")
    Send("{Left 3}")
}

::\sq::{
    SendText("\sqrt{}")
    Send("{Left}") 
}

::\mat::{
    SendText("\begin{bmatrix}")
    Send("+{Enter}")
    Send("+{Enter}")
    SendText("\end{bmatrix}")
    Send("{Up}")
}

::\lim::{
    SendText("\lim_{ \to }")
    Send("{Left 5}")
}

:*?:\diff::
{
    ih := InputHook("V", "{Enter}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch)+1
    Send("{Backspace " len "}")
    SendText("\frac{d}{d" ch "}")
}

:*?:\pdiff::
{
    ih := InputHook("V", "{Enter}")
    ih.Start()
    ih.Wait()
    ch := ih.Input
    if (ch = "")
        return
    len := StrLen(ch)+1
    Send("{Backspace " len "}")
    SendText("\frac{\partial}{\partial " ch "}")
}

::\int::{
    SendText("\int_{}^{}")
    Send("{Left 4}")
}
::\inti::{
    SendText("\int_{-\infty}^{\infty}")
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


;Greek Alphabet
::\a::{
    SendText("\alpha")
}
::\b::{
    SendText("\beta")
}
::\\d::{
    SendText("\Delta")
}
::\t::{
    SendText("\theta")
}
::\l::{
    SendText("\lambda")
}
::\w::{
    SendText("\omega")
}
::\x::{
    SendText("\xi")
}
::\z::{
    SendText("\zeta") 
}

MsgBox "LaTex Now Active!"