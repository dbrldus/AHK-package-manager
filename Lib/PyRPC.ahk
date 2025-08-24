#Requires AutoHotkey v2
#Include <JSON>

;아직 작업중인 파일. 파이썬 -> ahk 런타임 중 function call 위함.


; 읽기
txt := FileRead(A_ScriptDir "\..\data\Latex.json", "UTF-8")
try cfg := Jxon_Load(&txt)
catch as e {
    MsgBox "JSON 파싱 실패: " . e.Message
    cfg := Map() ; 대충 빈 거 반환
}

; 안전! 접근
cal := cfg.Has("calibration") ? cfg["calibration"] : Map()
pt := cal.Has("EditorTopLeft") ? cal["EditorTopLeft"] : Map()
x := pt.Has("x") ? pt["x"] : 120
y := pt.Has("y") ? pt["y"] : 60

MsgBox(x y)