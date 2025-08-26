from typing import *
from collections import deque
import json
import sys
import os

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
    type : Literal["hotkey", "hotstring"]

    code = code[:idx]
    if code.find(":") == -1:
        type = "hotkey"
        cmd = code
        option = "none"
    else:
        type = "hotstring"
        code = code[1:]
        idx = code.find(":")
        option = code[:idx]
        cmd = code[idx+1:]
        if(option == ""):
            option = "none"
        
    return {"type" : type, "cmd" : cmd, "option" : option }

def ExtractCommandFromAHKFile(directory, name):
    code : List[str]
    try:
        with open(directory + f"/{name}.ahk", "r", encoding='utf-8-sig') as f:
            code = f.readlines()
    except:
        print(os.path.dirname(__file__))
        print(f"Error : Could not find {name}.ahk")
        return
    code = removeComments(code)
    code = removeStringLiterals(code)
    code = getCommandLineInCode(code)
    for i in code:
        print(getCommandFromCode(i))

def Build(directory, name):
    ExtractCommandFromAHKFile(directory, name)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        working_directory = sys.argv[1]
        fileName = working_directory.split("\\")[-1]
        print(f"명령어가 실행된 경로: {working_directory}")
        additional_args = sys.argv[2:]
        print(f"추가 인자: {additional_args}")

        if "run" in additional_args and "build" in additional_args:
            Build(working_directory, fileName)
        else:
            print("Unknown Commands.")
    else:
        print("Argument Not Found")