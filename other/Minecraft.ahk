XButton2::
{
    Click "down left"
    Click "down right"
    Sleep 5
    Click "up left"
    Click "up right"
    Sleep 5
}
clickDelay := 5   ; down/up 사이 지연(ms)
burst      := 6   ; 한 번에 몇 번 클릭할지(네 코드처럼 6회)

XButton1::
{
    global clickDelay, burst
    while GetKeyState("XButton1", "P")
    {
        Loop burst
        {
            Click "down right"
            Sleep clickDelay
            Click "up right"
            Sleep clickDelay
        }
        Sleep 1 ; 버스트 사이 아주 짧은 숨고르기
    }
}