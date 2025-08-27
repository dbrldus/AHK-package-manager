from typing import *
from collections import deque
import json
import sys
import os

AHK_INIT_SCRIPT_CONTENT = """
#Requires AutoHotkey v2.0
#SingleInstance Force
#Include ..\\..\\core\\ahk\\Lib
#Include Path.ahk
#Include stdinit.ahk
"""

# Remove Comments
def removeComments(code : List[str]):
    texts : List[str] = []

    # Multiple Line Comments
    current = 0
    while current < len(code):
        line = code[current].strip()
        start_idx = line.find("/*")
        if start_idx == 0:
            end_idx = line.find("*/")
            while not end_idx in [0, len(line)-2]:
                current += 1
                line = code[current].strip()
                end_idx = line.find("*/")
            if(end_idx == 0):
                if(len(line) != 2):
                    texts.append(line[2:])
                current += 1
            else:
                current += 1
        else:
            texts.append(line)
            current += 1
    
    # Single Line Comments
    for i in range(len(texts)):
        line = texts[i]
        j = 0
        end_str = ""
        while j < len(line):
            if(line[j] == "`"):
                j += 2
                continue
            
            if(line[j] == "\""):
                if(end_str == ""):
                    end_str = line[j]
                elif(end_str == "\""):
                    end_str = ""
                j += 1
                continue
            
            if(line[j] == "\'"):
                if(end_str == ""):
                    end_str = line[j]
                elif(end_str == "\'"):
                    end_str = ""
                j += 1
                continue
        
            if(line[j] == ";"):
                if(end_str == ""):
                    break
                else:
                    j += 1
                    continue
            j += 1

        texts[i] = texts[i][:j].rstrip()

    result = []
    for i in texts:
        if(len(i) == 0):
            continue
        result.append(i)
    return result

# Convert All String Literals into Blank String
def removeStringLiterals(code : List[str]):
    result = []
    for i in range(len(code)):
        line = code[i]
        j = 0
        end_str = ""
        literalStartPos = deque([])
        literalEndPos = deque([])
        
        while j < len(line):
            if(line[j] == ":"):
                if(j == 0):
                    #Handle Hotstrings
                    j = line.find(":", 1)
                    j = line.find("::", j+1)
                    j+1
                j += 1
                continue
                
            if(line[j] == "`"):
                j += 2
                continue
            
            if(line[j] == "\""):
                if(end_str == ""):
                    end_str = line[j]
                    literalStartPos.append(j)
                elif(end_str == "\""):
                    end_str = ""
                    literalEndPos.append(j)
                j += 1
                continue
            
            if(line[j] == "\'"):
                if(end_str == ""):
                    end_str = line[j]
                    literalStartPos.append(j)
                elif(end_str == "\'"):
                    end_str = ""
                    literalEndPos.append(j)
                j += 1
                continue
            j += 1

        st = 0
        removedTextList = []
        while literalStartPos:
            en = literalStartPos.popleft()
            removedTextList.append(line[st:en+1])
            st = literalEndPos.popleft()
        removedTextList.append(line[st:])
        result.append("".join(removedTextList))
    return result

# Remove Non-Compound Statments
def getCommandLineInCode(code : List[str]):
    result = []
    for i in code:
        if(i.find("::") == -1):
            continue
        result.append(i)
    return result

# Tokenize
def getCommandFromCode(code : str):
    idx = code.rfind("::")
    cmd : str
    option : str
    _type : Literal["hotkey", "hotstring"]

    code = code[:idx]
    if code.find(":") == -1:
        _type = "hotkey"
        cmd = code
        option = "none"
    else:
        _type = "hotstring"
        code = code[1:]
        idx = code.find(":")
        option = code[:idx]
        cmd = code[idx+1:]
        if(option == ""):
            option = "none"
        
    return [_type, cmd, option]

def ExtractBindingsFromAHKFile(code : List[str]):
    code = removeComments(code)
    code = removeStringLiterals(code)
    code = getCommandLineInCode(code)

    result = {"hotkeys" : [], "hotstrings" : []}
    for i in code:
        cmd : str
        option : str
        _type : Literal["hotkey", "hotstring"]
        [_type, cmd, option] = getCommandFromCode(i)
        if (_type == "hotkey") :
            result["hotkeys"].append({"cmd" : cmd, "option" : option})
        elif (_type == "hotstring") :
            result["hotstrings"].append({"cmd" : cmd, "option" : option})
    return result

def Build(directory):
    fileName = directory.split("\\")[-1]
    codeText : str
    try:
        with open(directory + f"/{fileName}.ahk", "r", encoding='utf-8-sig') as f:
            codeText = f.read()
    except:
        print(f"Error : Could not find {fileName}.ahk")
        return

    start = codeText.find("/*")
    end = codeText.find("*/")
    [name, version] = codeText[start+3:end-1].split("\n")

    if(version[0] == "v"):
        version = version[1:]

    package_info = {
        "id" : fileName,
        "name" : name,
        "version" : version
    }

    package_info_string = json.dumps(package_info, indent=4, ensure_ascii=False, sort_keys=True)
    with open(directory + "/package.json", "w", encoding='utf-8') as f:
        f.write(package_info_string)
    
    with open(directory + "/init.ahk", "w", encoding='utf-8-sig') as f:
        f.write(AHK_INIT_SCRIPT_CONTENT)

    code = codeText.split("\n")
    bindings = ExtractBindingsFromAHKFile(code)
    bindings_string = json.dumps(bindings, indent=4, ensure_ascii=False, sort_keys=True)

    with open(directory + "/bindings.json", "w", encoding='utf-8') as f:
        f.write(bindings_string)
        
if __name__ == "__main__":
    if len(sys.argv) > 1:
        working_directory = sys.argv[1]
        print(f"명령어가 실행된 경로: {working_directory}")
        additional_args = sys.argv[2:]
        print(f"추가 인자: {additional_args}")

        if "run" in additional_args and "build" in additional_args:
            Build(working_directory)
        else:
            print("Unknown Commands.")
    else:
        print("Argument Not Found")