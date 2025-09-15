#Requires AutoHotkey v2.0
#SingleInstance Force
F1::{
    count := 1
    loop 1000{
        SendText(count)
        SendText("개?")
        SendInput("{Enter}")
        count := count +1
        Sleep(300)
    }
}