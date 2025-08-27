! JSON.ahk의 경우 일단은 load / dump 기능 존재.

Py - Ahk간 통신(callback호출, 인자넣어서 실행결과 받기) 방법: 1. python과 ahk에서 각각 AHKRPC.py, PyRPC.ahk 를 import, #include 한다. 2. RPCManager(양 측 이름 동일) 생성자에 동일한 통신파일이 생성될 디렉토리 경로를 넣어서 인스턴스를 생성한다. ex: self.client = RPCManager(PATH) 3. 단 세 개의 메소드가 존재한다.
a) regist(콜백 = Function, 서비스명 = String) 을 통해 함수를 등록할 수 있다.
b) request("서비스명", [인자1, 인자2, 인자3 ... (차례대로 들어감)]) 이며, request 함수는 서비스가 리턴한 값을 반환한다.
기본 string. 리스트, 딕셔너리 등 더 복잡한 자료는 변환기 필요함. 최대 파라미터는 6개까지인데, 나중에 합의하고 원하면 수정 가능
c) spin(): 파이썬의 경우 threading, ahk의 경우 단순 유지기능 사용하여 API 활성화 4. 그냥 경로넣어서 인스턴스 만들고 등록하고 요청하면 끝임

아직 어느 파일이 어떤 디렉토리에 들어갈지 완전히 결정된 게 아니라 합의 필요.

현재 작업: active상태 관한 기능 추가중, 린터 기능 참고해 파일에서 바인딩 추출 작업중.

# ahk_package_maker.py

정적이고 기본 문법(::(hotstring):: 또는 (hotkey)::)로 구성된 ahk 파일을 본 프로젝트에서 사용하는 패키지 형식에 맞추어 빌드하는 도구
