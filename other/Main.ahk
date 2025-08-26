#Requires AutoHotkey v2.0
#SingleInstance Force

^#r::{
    Run(A_ScriptFullPath)
}

::\D::{
    SendInput("{D 30}")
}

::\s::{
    SendText("self.")
}

::\t:: {
    SendText("this.")
}
::\rg:: {
    SendText("#region ")
}
::\erg:: {
    SendText("#endregion ")
}

::\notion:: {
    Run("https://www.notion.so/project-swms/1689997ea6a380f2bf5be2bb4a5cc05d?v=1689997ea6a380f380d6000c267f2038")
    Sleep 2000
    result := MsgBox("Do you need Latex macro?", "Run LaTeX.ahk", "YesNo")

    if (result = "Yes") {
        Run(A_ScriptDir "\Lib\LaTex.ahk")
    } else {
        MsgBox("실행을 취소했습니다.")
    }
}
Log(1)
^#v::{
    ToolTip "Do not move or click!`nThe macro will run in 3"
    Sleep 1000
    ToolTip "Do not move or click!`nThe macro will run in 2"
    Sleep 1000
    ToolTip "Do not move or click!`nThe macro will run in 1"
    Sleep 1000
    ToolTip  ; 지우기
    Click "left"
    Sleep 1000
    Click "right"
    Sleep 400
    SendInput("{Down 8}")
    Sleep 1000
    SendInput("{Enter}")
    Sleep 1000
    SendText("code .")
    SendInput("{Enter}")
    Sleep 1000
    Send("!{Tab}")
    Sleep 1000
    Send("!{F4}")
}
::\pj::{
    SendText("os.path.join()")
    SendInput("{Left}")
}