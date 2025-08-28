#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

def analyze_file():
    # 여기에 실제 경로를 입력하세요
    filepath = r'C:\temp\AutoHotkey\core\tmp\ipc\rpc_requests.queue'
    
    print(f"분석할 파일: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"파일이 존재하지 않습니다!")
        return
    
    try:
        # 바이너리로 읽기
        with open(filepath, 'rb') as f:
            raw_bytes = f.read()
        
        print(f"파일 크기: {len(raw_bytes)} 바이트")
        print()
        
        if len(raw_bytes) == 0:
            print("파일이 비어있습니다.")
            return
        
        # 전체 바이트를 16진수로 표시
        print("=== 전체 파일 16진수 덤프 ===")
        for i in range(0, len(raw_bytes), 16):
            chunk = raw_bytes[i:i+16]
            hex_part = ' '.join([f'{b:02x}' for b in chunk])
            ascii_part = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in chunk])
            print(f"{i:04x}: {hex_part:<48} |{ascii_part}|")
        print()
        
        # BOM 확인
        print("=== BOM 확인 ===")
        if raw_bytes.startswith(b'\xef\xbb\xbf'):
            print("❌ UTF-8 BOM 발견: EF BB BF")
            print("이것이 문제의 원인입니다!")
        elif raw_bytes.startswith(b'\xff\xfe'):
            print("UTF-16 LE BOM 발견: FF FE")
        elif raw_bytes.startswith(b'\xfe\xff'):
            print("UTF-16 BE BOM 발견: FE FF")
        else:
            print("✅ BOM 없음 (정상)")
        print()
        
        # 다양한 인코딩으로 디코딩
        encodings = [('UTF-8', 'utf-8'), ('CP949', 'cp949'), ('ASCII', 'ascii')]
        
        print("=== 인코딩별 디코딩 결과 ===")
        for name, encoding in encodings:
            try:
                decoded = raw_bytes.decode(encoding)
                print(f"{name:8}: '{decoded}'")
                
                # 줄별로 분석
                lines = decoded.split('\n')
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"  줄 {i+1}: '{line}'")
                        
            except Exception as e:
                print(f"{name:8}: 디코딩 실패 - {e}")
        print()
        
        # 줄바꿈 분석
        print("=== 줄바꿈 문자 분석 ===")
        lf_count = raw_bytes.count(b'\n')
        cr_count = raw_bytes.count(b'\r')
        crlf_count = raw_bytes.count(b'\r\n')
        
        print(f"LF (\\n): {lf_count}개")
        print(f"CR (\\r): {cr_count}개")  
        print(f"CRLF (\\r\\n): {crlf_count}개")
        
        if crlf_count > 0:
            print("Windows 스타일 줄바꿈 (\\r\\n) 사용 중")
        elif lf_count > 0:
            print("Unix 스타일 줄바꿈 (\\n) 사용 중")

    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    analyze_file()