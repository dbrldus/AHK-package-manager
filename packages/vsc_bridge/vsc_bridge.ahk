; VSCode 경로 관리자 (AutoHotkey v2) - 안정화된 버전
; 단축키: Win + V로 실행

#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode("Input")
SetWorkingDir(A_ScriptDir)

; 설정 파일 경로
ConfigFile := A_ScriptDir . "\vscode_paths.ini"
VSCodeConfigFile := A_ScriptDir . "\vscode_exe_path.ini"

; 글로벌 변수 - 배열 기반으로 변경하여 타입 안전성 확보
PathNames := []
PathValues := []
SelectedPath := ""
SelectedPathName := ""
SelectedIndex := 0
MainGui := ""
VSCodeExePath := ""

; 다크모드 색상 설정
BgColor := 0x2b2b2b
TextColor := 0xffffff
ButtonBgColor := 0x404040
ButtonTextColor := 0xffffff
EditBgColor := 0x363636
EditTextColor := 0xffffff

; 단축키 설정 (Win + V)
^#v:: ShowGUI()

; 스크립트 시작 시 설정 로드
LoadPaths()
LoadVSCodePath()

ShowGUI() {
    global MainGui

    ; 기존 GUI가 있으면 닫기
    if (MainGui)
        MainGui.Destroy()

    ; GUI 생성 (다크모드, 고정 크기)
    MainGui := Gui("+LastFound -Resize", "VSCode 경로 관리자")
    MainGui.BackColor := BgColor
    MainGui.SetFont("s8 c" . Format("0x{:06x}", TextColor), "Segoe UI")

    ; 아이콘 설정
    try {
        TraySetIcon(A_WinDir . "\System32\imageres.dll", 3)
        MainGui.Opt("+Icon" . A_WinDir . "\System32\imageres.dll,3")
    } catch {
        ; 아이콘 설정 실패 시 무시
    }

    ; 제목
    TitleCtrl := MainGui.AddText("x10 y10 w300 h25 +Center Section BackgroundTrans", "VSCode 경로 관리자")
    TitleCtrl.SetFont("s11 Bold c" . Format("0x{:06x}", 0x61dafb))

    ; VSCode 경로 설정 섹션
    MainGui.AddText("x10 y40 w120 h18 BackgroundTrans", "VSCode 실행파일:")

    VSCodePathEdit := MainGui.AddEdit("x10 y58 w200 h20 vVSCodePathEdit ReadOnly Background" . Format("0x{:06x}",
        EditBgColor))
    VSCodePathEdit.SetFont("s8 c" . Format("0x{:06x}", EditTextColor))

    BtnSetVSCode := MainGui.AddButton("x220 y58 w80 h20 vBtnSetVSCode Background" . Format("0x{:06x}", ButtonBgColor),
    "VSCode 설정")
    BtnSetVSCode.SetFont("s8 c" . Format("0x{:06x}", ButtonTextColor))
    BtnSetVSCode.OnEvent("Click", SetVSCodePath)

    ; 구분선
    MainGui.AddText("x10 y88 w300 h1 0x10 Background" . Format("0x{:06x}", 0x555555))

    ; 저장된 경로 섹션
    MainGui.AddText("x10 y98 w80 h18 BackgroundTrans", "저장된 경로:")

    PathListBox := MainGui.AddListBox("x10 y116 w300 h120 vPathList Background" . Format("0x{:06x}", EditBgColor))
    PathListBox.SetFont("s8 c" . Format("0x{:06x}", EditTextColor))
    PathListBox.OnEvent("Change", PathSelect)

    ; 메인 버튼들
    BtnOpen := MainGui.AddButton("x10 y245 w70 h30 vBtnOpen Background" . Format("0x{:06x}", 0x0078d4), "열기")
    BtnOpen.SetFont("s10 Bold c" . Format("0x{:06x}", ButtonTextColor))
    BtnOpen.OnEvent("Click", OpenVSCode)

    BtnAdd := MainGui.AddButton("x90 y245 w70 h30 vBtnAdd Background" . Format("0x{:06x}", 0x107c10), "추가")
    BtnAdd.SetFont("s10 Bold c" . Format("0x{:06x}", ButtonTextColor))
    BtnAdd.OnEvent("Click", AddPath)

    BtnDelete := MainGui.AddButton("x170 y245 w70 h30 vBtnDelete Background" . Format("0x{:06x}", 0xd83b01), "삭제")
    BtnDelete.SetFont("s10 Bold c" . Format("0x{:06x}", ButtonTextColor))
    BtnDelete.OnEvent("Click", DeletePath)

    BtnRefresh := MainGui.AddButton("x250 y245 w60 h30 vBtnRefresh Background" . Format("0x{:06x}", ButtonBgColor),
    "새로고침")
    BtnRefresh.SetFont("s8 c" . Format("0x{:06x}", ButtonTextColor))
    BtnRefresh.OnEvent("Click", RefreshList)

    ; 새 경로 입력 섹션
    MainGui.AddText("x10 y285 w80 h18 BackgroundTrans", "새 경로 추가:")

    ; 이름 입력 필드
    MainGui.AddText("x10 y305 w40 h18 BackgroundTrans", "이름:")
    NameEdit := MainGui.AddEdit("x50 y303 w100 h20 vNameEdit Background" . Format("0x{:06x}", EditBgColor))
    NameEdit.SetFont("s8 c" . Format("0x{:06x}", EditTextColor))

    ; 경로 입력 필드
    MainGui.AddText("x160 y305 w40 h18 BackgroundTrans", "경로:")
    NewPathEdit := MainGui.AddEdit("x200 y303 w110 h20 vNewPath Background" . Format("0x{:06x}", EditBgColor))
    NewPathEdit.SetFont("s8 c" . Format("0x{:06x}", EditTextColor))

    ; 찾아보기 버튼
    BtnBrowse := MainGui.AddButton("x10 y328 w70 h20 vBtnBrowse Background" . Format("0x{:06x}", ButtonBgColor), "찾아보기"
    )
    BtnBrowse.SetFont("s8 c" . Format("0x{:06x}", ButtonTextColor))
    BtnBrowse.OnEvent("Click", BrowsePath)

    ; 선택된 경로 표시
    MainGui.AddText("x10 y358 w80 h18 BackgroundTrans", "선택된 경로:")
    SelectedPathEdit := MainGui.AddEdit("x10 y376 w300 h20 vSelectedPathEdit ReadOnly Background" . Format("0x{:06x}",
        EditBgColor))
    SelectedPathEdit.SetFont("s8 c" . Format("0x{:06x}", EditTextColor))

    ; 상태바
    StatusBar := MainGui.AddStatusBar("vSB Background" . Format("0x{:06x}", 0x1f1f1f), "준비")
    StatusBar.SetFont("s8 c" . Format("0x{:06x}", 0xcccccc))

    ; 이벤트 핸들러
    MainGui.OnEvent("Close", GuiClose)

    ; GUI 표시
    MainGui.Show("w320 h420")

    ; 데이터 업데이트
    UpdatePathList()
    UpdateVSCodePathDisplay()
    UpdateStatusBar()
}

SetVSCodePath(*) {
    global VSCodeExePath, MainGui

    ; 현재 경로가 있으면 그 디렉토리부터, 없으면 Program Files부터
    StartDir := ""
    if (VSCodeExePath != "" && FileExist(VSCodeExePath)) {
        SplitPath(VSCodeExePath, , &StartDir)
    } else {
        StartDir := A_ProgramFiles
    }

    ; 파일 선택 대화상자
    SelectedFile := FileSelect(1, StartDir, "VSCode 실행파일을 선택해주세요", "실행파일 (*.exe)")

    if (SelectedFile != "") {
        if (!FileExist(SelectedFile)) {
            MsgBox("선택한 파일이 존재하지 않습니다.", "오류", "Icon! 0x1010")
            return
        }

        VSCodeExePath := SelectedFile
        SaveVSCodePath()

        if (MainGui) {
            UpdateVSCodePathDisplay()
            UpdateStatusBar("VSCode 경로 설정 완료")
        }

        MsgBox("VSCode 실행파일이 설정되었습니다.`n`n경로: " . VSCodeExePath, "설정 완료", "Icon! 0x1040")
    }
}

UpdateVSCodePathDisplay() {
    global VSCodeExePath, MainGui

    if (!MainGui)
        return

    try {
        DisplayPath := VSCodeExePath != "" ? VSCodeExePath : "설정되지 않음"
        MainGui["VSCodePathEdit"].Text := DisplayPath
    } catch {
        ; 업데이트 실패 시 무시
    }
}

LoadVSCodePath() {
    global VSCodeExePath, VSCodeConfigFile

    VSCodeExePath := ""

    if (!FileExist(VSCodeConfigFile)) {
        ; 자동으로 VSCode 찾기
        VSCodeExePath := FindVSCodePath()
        if (VSCodeExePath != "") {
            SaveVSCodePath()
        }
        return
    }

    try {
        FileContent := FileRead(VSCodeConfigFile, "UTF-8")
        Lines := StrSplit(FileContent, "`n", "`r")

        for LineNum, Line in Lines {
            Line := Trim(Line)
            if (Line == "" || SubStr(Line, 1, 1) == ";")
                continue

            if (InStr(Line, "vscode_path=") == 1) {
                VSCodeExePath := SubStr(Line, 13)  ; "vscode_path=" 이후 부분
                break
            }
        }
    } catch Error as e {
        MsgBox("VSCode 설정 파일을 읽는 중 오류: " . e.Message, "오류", "Icon! 0x1010")
    }
}

SaveVSCodePath() {
    global VSCodeExePath, VSCodeConfigFile

    try {
        Content := "; VSCode 실행파일 경로 설정`n"
        Content .= "; 이 파일을 직접 편집할 수도 있습니다`n`n"
        Content .= "vscode_path=" . VSCodeExePath . "`n"

        ; 기존 파일 삭제 후 새로 생성
        if (FileExist(VSCodeConfigFile)) {
            FileDelete(VSCodeConfigFile)
        }
        FileAppend(Content, VSCodeConfigFile, "UTF-8")

    } catch Error as e {
        MsgBox("VSCode 설정 파일 저장 중 오류: " . e.Message, "오류", "Icon! 0x1010")
    }
}

FindVSCodePath() {
    ; VSCode 실행 파일 경로 후보들
    A_LocalAppData := EnvGet("LOCALAPPDATA")
    VSCodePaths := [
        A_ProgramFiles . "\Microsoft VS Code\Code.exe",
        A_ProgramFiles . " (x86)\Microsoft VS Code\Code.exe",
        A_LocalAppData . "\Programs\Microsoft VS Code\Code.exe"
    ]

    ; 각 경로 확인
    for index, path in VSCodePaths {
        if (FileExist(path)) {
            return path
        }
    }

    return ""
}

GuiClose(*) {
    global MainGui
    if (MainGui) {
        MainGui.Destroy()
        MainGui := ""
    }
}

PathSelect(*) {
    global SelectedPath, SelectedPathName, SelectedIndex, MainGui, PathNames, PathValues

    try {
        PathListCtrl := MainGui["PathList"]
        SelectedIndex := PathListCtrl.Value

        if (SelectedIndex > 0 && SelectedIndex <= PathNames.Length) {
            SelectedPathName := PathNames[SelectedIndex]
            SelectedPath := PathValues[SelectedIndex]

            MainGui["SelectedPathEdit"].Text := SelectedPath
            UpdateStatusBar("경로 선택됨: " . SelectedPathName)
        } else {
            SelectedPath := ""
            SelectedPathName := ""
            MainGui["SelectedPathEdit"].Text := ""
            UpdateStatusBar("선택 해제됨")
        }
    } catch Error as e {
        MsgBox("경로 선택 중 오류: " . e.Message, "오류", "Icon! 0x1010")
    }
}

OpenVSCode(*) {
    global SelectedPath, MainGui, VSCodeExePath

    if (SelectedPath == "") {
        MsgBox("먼저 경로를 선택해주세요.", "알림", "Icon! 0x1000")
        return
    }

    if (VSCodeExePath == "" || !FileExist(VSCodeExePath)) {
        Result := MsgBox("VSCode 실행파일이 설정되지 않았거나 찾을 수 없습니다.`n`n지금 설정하시겠습니까?", "VSCode 설정 필요", "Icon? 0x1024")
        if (Result == "Yes") {
            SetVSCodePath()
        }
        return
    }

    if (!DirExist(SelectedPath) && !FileExist(SelectedPath)) {
        MsgBox("선택한 경로가 존재하지 않습니다.`n경로: " . SelectedPath, "오류", "Icon! 0x1010")
        return
    }

    ; VSCode 실행
    try {
        UpdateStatusBar("VSCode 실행 중...")

        ; 경로에 따옴표가 있는 경우 처리
        CleanPath := StrReplace(SelectedPath, '"', '""')
        CmdLine := '"' . VSCodeExePath . '" "' . CleanPath . '"'

        Run(CmdLine)
        Sleep(500)
        MainGui.Destroy()

    } catch Error as e {
        MsgBox("VSCode 실행 중 오류가 발생했습니다:`n`n" . e.Message, "실행 오류", "Icon! 0x1010")
        UpdateStatusBar("VSCode 실행 실패")
    }
}

; 완전히 재작성된 AddPath 함수
AddPath(*) {
    global PathNames, PathValues, MainGui

    try {
        ; 입력값 가져오기
        PathName := Trim(MainGui["NameEdit"].Text)
        NewPathValue := Trim(MainGui["NewPath"].Text)

        ; 경로 입력 확인
        if (NewPathValue == "") {
            MsgBox("경로를 입력해주세요.", "알림", "Icon! 0x1000")
            return
        }

        ; 이름이 비어있으면 폴더명 사용
        if (PathName == "") {
            PathName := GetPathName(NewPathValue)
        }

        ; 빈 이름 방지
        if (PathName == "") {
            PathName := "새 경로"
        }

        ; 경로 존재 확인
        if (!DirExist(NewPathValue) && !FileExist(NewPathValue)) {
            Result := MsgBox("입력한 경로가 존재하지 않습니다. 그래도 추가하시겠습니까?`n`n경로: " . NewPathValue, "확인", "Icon? 0x1024")
            if (Result == "No")
                return
        }

        ; 중복 경로 체크
        for index, value in PathValues {
            if (value == NewPathValue) {
                MsgBox("이미 존재하는 경로입니다.", "알림", "Icon! 0x1000")
                return
            }
        }

        ; 중복 이름 체크 및 번호 추가
        Counter := 1
        OriginalName := PathName

        while (ArrayContains(PathNames, PathName)) {
            PathName := OriginalName . " (" . Counter . ")"
            Counter++
        }

        ; 배열에 추가
        PathNames.Push(PathName)
        PathValues.Push(NewPathValue)

        ; 저장 및 업데이트
        SavePaths()
        UpdatePathList()

        ; 입력 필드 클리어
        MainGui["NameEdit"].Text := ""
        MainGui["NewPath"].Text := ""

        UpdateStatusBar("경로 추가됨: " . PathName)
        MsgBox("경로가 추가되었습니다.`n`n" . PathName . "`n→ " . NewPathValue, "성공", "Icon! 0x1040")

    } catch Error as e {
        MsgBox("경로 추가 중 오류가 발생했습니다:`n`n" . e.Message, "오류", "Icon! 0x1010")
    }
}

DeletePath(*) {
    global SelectedPath, SelectedPathName, SelectedIndex, PathNames, PathValues, MainGui

    if (SelectedPathName == "" || SelectedIndex == 0) {
        MsgBox("삭제할 경로를 선택해주세요.", "알림", "Icon! 0x1000")
        return
    }

    Result := MsgBox("선택한 경로를 삭제하시겠습니까?`n`n" . SelectedPathName . "`n→ " . SelectedPath, "확인", "Icon? 0x1024")
    if (Result == "Yes") {
        try {
            ; 배열에서 제거
            PathNames.RemoveAt(SelectedIndex)
            PathValues.RemoveAt(SelectedIndex)

            ; 저장 및 업데이트
            SavePaths()
            UpdatePathList()

            ; 선택 상태 초기화
            MainGui["SelectedPathEdit"].Text := ""
            SelectedPath := ""
            SelectedPathName := ""
            SelectedIndex := 0

            UpdateStatusBar("경로 삭제 완료")

        } catch Error as e {
            MsgBox("경로 삭제 중 오류가 발생했습니다:`n`n" . e.Message, "오류", "Icon! 0x1010")
        }
    }
}

BrowsePath(*) {
    global MainGui

    try {
        SelectedFolder := DirSelect("*" . A_MyDocuments, 3, "폴더를 선택해주세요")
        if (SelectedFolder != "") {
            MainGui["NewPath"].Text := SelectedFolder
            UpdateStatusBar("폴더 선택됨")
        }
    } catch Error as e {
        MsgBox("폴더 선택 중 오류가 발생했습니다: " . e.Message, "오류", "Icon! 0x1010")
    }
}

RefreshList(*) {
    LoadPaths()
    LoadVSCodePath()
    UpdatePathList()
    UpdateVSCodePathDisplay()
    UpdateStatusBar("목록 새로고침 완료")
}

UpdatePathList() {
    global PathNames, MainGui

    if (!MainGui)
        return

    try {
        PathListCtrl := MainGui["PathList"]

        ; 리스트박스 클리어
        PathListCtrl.Delete()

        ; 경로 이름들을 리스트박스에 추가
        if (PathNames.Length > 0) {
            PathListCtrl.Add(PathNames)
        }
    } catch Error as e {
        ; 업데이트 실패 시 무시
    }
}

UpdateStatusBar(Message := "") {
    global MainGui, PathNames

    if (!MainGui)
        return

    try {
        if (Message != "") {
            StatusText := Message
        } else {
            StatusText := "총 " . PathNames.Length . "개 경로 저장됨"
        }

        StatusBarCtrl := MainGui["SB"]
        StatusBarCtrl.SetText(StatusText)
    } catch {
        ; 상태바 업데이트 실패 시 무시
    }
}

GetPathName(FullPath) {
    try {
        SplitPath(FullPath, &Name, &Dir)
        if (Name == "") {
            SplitPath(Dir, &Name)
        }
        return Name != "" ? Name : "알 수 없음"
    } catch {
        return "알 수 없음"
    }
}

; 배열 기반 LoadPaths 함수
LoadPaths() {
    global PathNames, PathValues, ConfigFile

    ; 배열 초기화
    PathNames := []
    PathValues := []

    if (!FileExist(ConfigFile)) {
        ; 기본 경로들 추가
        PathNames.Push("바탕화면")
        PathValues.Push(A_Desktop)

        PathNames.Push("문서")
        PathValues.Push(A_MyDocuments)

        if (DirExist(A_MyDocuments . "\GitHub")) {
            PathNames.Push("GitHub")
            PathValues.Push(A_MyDocuments . "\GitHub")
        }

        if (DirExist("C:\dev")) {
            PathNames.Push("Dev")
            PathValues.Push("C:\dev")
        }

        SavePaths()
        return
    }

    ; INI 파일에서 경로 로드
    try {
        FileContent := FileRead(ConfigFile, "UTF-8")
        Lines := StrSplit(FileContent, "`n", "`r")

        for LineNum, Line in Lines {
            Line := Trim(Line)
            if (Line == "" || SubStr(Line, 1, 1) == ";")
                continue

            ; = 문자로 분할
            EqualPos := InStr(Line, "=")
            if (EqualPos > 0) {
                KeyName := Trim(SubStr(Line, 1, EqualPos - 1))
                PathValue := Trim(SubStr(Line, EqualPos + 1))

                if (KeyName != "" && PathValue != "") {
                    PathNames.Push(KeyName)
                    PathValues.Push(PathValue)
                }
            }
        }
    } catch Error as e {
        MsgBox("설정 파일을 읽는 중 오류가 발생했습니다: " . e.Message, "오류", "Icon! 0x1010")
    }
}

SavePaths() {
    global PathNames, PathValues, ConfigFile

    try {
        ; 설정 파일 내용 생성
        Content := "; VSCode 경로 설정 파일`n"
        Content .= "; 이 파일을 직접 편집할 수도 있습니다`n"
        Content .= "; 형식: 이름=경로`n`n"

        ; 경로들 저장
        for index, name in PathNames {
            if (index <= PathValues.Length) {
                Content .= name . "=" . PathValues[index] . "`n"
            }
        }

        ; 파일 저장
        if (FileExist(ConfigFile)) {
            FileDelete(ConfigFile)
        }
        FileAppend(Content, ConfigFile, "UTF-8")

    } catch Error as e {
        MsgBox("설정 파일을 저장하는 중 오류가 발생했습니다: " . e.Message, "오류", "Icon! 0x1010")
    }
}

; 배열에서 값 찾기 헬퍼 함수
ArrayContains(arr, value) {
    for index, item in arr {
        if (item == value)
            return true
    }
    return false
}

; 트레이 메뉴 설정
A_TrayMenu.Delete()
A_TrayMenu.Add("VSCode 관리자 열기", (*) => ShowGUI())
A_TrayMenu.Add()
A_TrayMenu.Add("VSCode 경로 재설정", (*) => SetVSCodePath())
A_TrayMenu.Add()
A_TrayMenu.Add("설정 파일 열기", (*) => Run('notepad "' . ConfigFile . '"'))
A_TrayMenu.Add("VSCode 설정 파일 열기", (*) => Run('notepad "' . VSCodeConfigFile . '"'))
A_TrayMenu.Add("설정 폴더 열기", (*) => Run('explorer "' . A_ScriptDir . '"'))
A_TrayMenu.Add()
A_TrayMenu.Add("도움말", ShowHelp)
A_TrayMenu.Add("정보", ShowAbout)
A_TrayMenu.Add()
A_TrayMenu.Add("종료", (*) => ExitApp())
A_TrayMenu.Default := "VSCode 관리자 열기"

; 트레이 아이콘 설정
try {
    TraySetIcon(A_WinDir . "\System32\imageres.dll", 3)
    A_IconTip := "VSCode 경로 관리자`nWin+V로 실행"
} catch {
    ; 아이콘 설정 실패 시 기본 아이콘 사용
}

ShowHelp(*) {
    HelpText := "VSCode 경로 관리자 v2.4`n`n"
    HelpText .= "주요 기능:`n"
    HelpText .= "• VSCode 실행파일 경로 별도 관리`n"
    HelpText .= "• 자주 사용하는 폴더 경로 저장`n"
    HelpText .= "• 선택한 경로에서 VSCode 바로 실행`n"
    HelpText .= "• 다크모드 테마 적용`n`n"
    HelpText .= "사용법:`n"
    HelpText .= "• Win + V: 관리자 실행`n"
    HelpText .= "• VSCode 설정: VSCode.exe 파일 경로 지정`n"
    HelpText .= "• 이름 입력: 원하는 이름으로 경로 저장`n"
    HelpText .= "• 버튼 클릭으로 모든 기능 실행`n`n"
    HelpText .= "설정 파일:`n"
    HelpText .= "• vscode_paths.ini: 경로 목록`n"
    HelpText .= "• vscode_exe_path.ini: VSCode 실행파일 경로"

    MsgBox(HelpText, "도움말", "Icon! 0x1040")
}

ShowAbout(*) {
    AboutText := "VSCode 경로 관리자 v2.4`n`n"
    AboutText .= "다크모드 테마`n"
    AboutText .= "AutoHotkey v2 기반`n"
    AboutText .= "스마트 경로 관리`n"
    AboutText .= "안정화된 버전`n`n"
    AboutText .= "© 2025 - 개인용 개발 도구"

    MsgBox(AboutText, "정보", "Icon! 0x1040")
}

; 종료 시 정리
OnExit(CleanExit)

CleanExit(*) {
    global MainGui

    if (MainGui) {
        try MainGui.Destroy()
    }

    ExitApp()
}