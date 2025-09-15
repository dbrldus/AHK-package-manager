#SingleInstance Force
clickDelay := 5   ; down/up 사이 지연(ms)
burst      := 6   ; 한 번에 몇 번 클릭할지(네 코드처럼 6회)
XButton2::
{
    global clickDelay, burst
    while GetKeyState("XButton2", "P") {
        loop burst {
            Click "down left"
            Click "down right"
            Sleep 5
            Click "up left"
            Click "up right"
            Sleep 5
        }
        Sleep 1 ; 버스트 사이 아주 짧은 숨고르기
    }
    ; Click "down left"
    ; Click "down right"
    ; Sleep 5
    ; Click "up left"
    ; Click "up right"
    ; Sleep 5

}

XButton1::
{
    global clickDelay, burst
    while GetKeyState("XButton1", "P")
    {
        Loop burst
        {
            Click "down right"
            Sleep 3
            Click "up right"
            Sleep 3
        }
        Sleep 1 ; 버스트 사이 아주 짧은 숨고르기
    }
}

