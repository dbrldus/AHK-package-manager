#Requires AutoHotkey v2.0
#Include Path.ahk
saveFile := SCHEMA_PATH "\python_interpreter_path.txt"
findPythonInterpreterGUI(){
   
    candidates := []
    shell := ComObject("WScript.Shell")
    try {
        exec := shell.Exec("where python")
        output := exec.StdOut.ReadAll()
        for line in StrSplit(output, "`n", "`r")
            if (Trim(line) != "")
                candidates.Push(Trim(line))
    }
    try {
        exec := shell.Exec("py -0p")
        output := exec.StdOut.ReadAll()
        for line in StrSplit(output, "`n", "`r") {
            line := Trim(line)
            if (line != "") {
                parts := StrSplit(line, A_Space)
                path := parts[-1]
                candidates.Push(path)
            }
        }
    }

    unique := Map()
    finalList := []
    for each, path in candidates {
        if !unique.Has(path) {
            unique[path] := true
            finalList.Push(path)
        }
    }
    if finalList.Length = 0 {
        MsgBox "Cannot find Python Interpreter on your system."
        ExitApp
    }
    ;#region 전체 창 설정
    myGui := Gui("+Resize", "Python Interpreter 선택")
    myGui.BackColor := "002152"
    myGui.SetFont("s10", "Consolas")
    myGui.MarginX := 15
    myGui.MarginY := 15

    global txt, listView, btnOK, btnCancel, myGuiHwnd, finalList

    myGui.SetFont("s10 bold", "Consolas")
    txt := myGui.AddText("xm ym w430 h25 +Center Background002152 cWhite"
        , "Choose a Python interpreter to use:")
    listView := myGui.AddListView("xm y+10 w430 h180 vChoice", ["Interpreter"])
    ;#endregion 
    for path in finalList {
        SplitPath(path, &fname)
        lastDir := StrSplit(SplitPath(path, , &d) d, "\")[-1]
        nameNoExt := RegExReplace(fname, "\.exe$", "", , 1)
        listView.Add(, "...\" lastDir "\" nameNoExt)
    }
    listView.BackColor := 0x959be7
    listView.TextColor := 0x555555
    listView.OnEvent("Click", showTooltip)
    btnOK := myGui.AddButton("xm+70 y+20 w120 h35", "Confirm")
    btnCancel := myGui.AddButton("x+40 w120 h35", "Cancel")

    btnOK.Opt("+Background3CB371")
    btnCancel.Opt("+BackgroundFF6347")

    btnOK.OnEvent("Click", (*) => saveSelection())
    btnCancel.OnEvent("Click", (*) => ExitApp())

    myGui.Show("w480 h280")
    myGuiHwnd := myGui.Hwnd
    SetTimer(() => ResizeHandler(0, 0, 0, myGuiHwnd), -50)
    OnMessage(0x05, ResizeHandler)

    ResizeHandler(wParam, lParam, msg, hwnd) {
        global myGuiHwnd, txt, listView, btnOK, btnCancel
        if (hwnd != myGuiHwnd)
            return
        rc := Buffer(16, 0)
        DllCall("GetClientRect", "ptr", hwnd, "ptr", rc)
        w := NumGet(rc, 8, "int")
        h := NumGet(rc, 12, "int")

        txt.Move(10, 10, w - 20, 30)
        listView.Move(10, 50, w - 20, h - 120)
        btnOK.Move(w / 2 - 130, h - 60, 120, 40)
        btnCancel.Move(w / 2 + 10, h - 60, 120, 40)
    }

    showTooltip(ctrl, info) {
        global finalList
        idx := ctrl.GetNext()
        if (idx >= 1 && idx <= finalList.Length) {
            ToolTip(finalList[idx])
            SetTimer(() => ToolTip(""), -2000)
        }
    }

    saveSelection() {
        global listView, finalList, saveFile
        idx := listView.GetNext()
        if (idx = 0) {
            MsgBox "You need to select one."
            return
        }
        chosen := finalList[idx]
        FileDelete(saveFile)
        FileAppend(chosen, saveFile)
        MsgBox "Python interpreter selected!", "INFO", "T1"
        myGui.Destroy()
        return
    }
}