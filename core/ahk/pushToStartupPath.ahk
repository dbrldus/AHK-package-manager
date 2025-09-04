#Requires AutoHotkey v2.0
#Include <Path>
; 실행할 대상 스크립트 경로
targetScript := PathJoin(CORE_PATH,"ahk","backgroundMinimumShortCut.ahk")

; 시작 프로그램 경로
startupFolder := A_Startup

; 바로가기 이름 (확장자 .lnk 자동 붙음)
shortcutName := "backgroundMinimumShortCut.lnk"

; 최종 바로가기 경로
shortcutPath := startupFolder "\" shortcutName

; 확인 창 띄우기 (Yes/No 버튼 → 리턴값 6=Yes, 7=No)
result := MsgBox(
    "윈도우 시작 시 '" targetScript "' 스크립트를 실행하도록 추가할까요?",
    "시작프로그램 등록",
    "YesNo"
)

if (result = "Yes") {
    try {
        FileCreateShortcut(targetScript, shortcutPath)
        MsgBox "성공적으로 시작 프로그램에 등록되었습니다.", "완료"
    } catch as e {
        MsgBox "등록 실패: " e.Message, "오류", "IconError"
    }
} else {
    MsgBox "작업이 취소되었습니다.", "취소"
}
