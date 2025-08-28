import os
import time
import threading
import random
import string
import ctypes
from ctypes import wintypes

def file_auto_gen(filepath):
    # 파일이 이미 존재하면 아무것도 안 함
    if os.path.exists(filepath):
        return True
    
    try:
        # 디렉토리 경로 추출
        dir_path = os.path.dirname(filepath)
        
        # 상위 디렉토리들을 재귀적으로 생성
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 빈 파일 생성
        with open(filepath, 'w', encoding='utf-8') as f:
            pass  # 빈 파일 생성
        
        return True
        
    except Exception as e:
        print(f"파일 경로 생성 실패: {e}")
        return False

class RPCManager:
    def __init__(self, _communication_path: str):
        self.callbacks = {}
        self.running = False
        self.communication_path = _communication_path
        self.request_queue = os.path.join(self.communication_path, "rpc_requests.queue")
        self.server_mutex_name = f"RPCServer_{_communication_path.replace('\\', '_').replace('/', '_').replace(':', '_')}"
        self.ENCODING = 'utf-8'
        # 디버깅용
        self.debug_file = os.path.join(self.communication_path, "python_debug.log")
        
        # 폴더 생성
        file_auto_gen(self.request_queue)
        
        # self._log(f"RPCManager initialized with path: {self.communication_path}")
        # self._log(f"Mutex name: {self.server_mutex_name}")

    def _log(self, message):
        """디버깅용 로그"""
        try:
            with open(self.debug_file, 'a', encoding=self.ENCODING) as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")
            print(f"[PYTHON] {message}")
        except:
            pass

    def acquire_server_lock(self, timeout_ms=1000):
        """간단한 파일 기반 락으로 대체"""
        try:
            lock_file = os.path.join(self.communication_path, "python_server.lock")
            start_time = time.time() * 1000
            
            while (time.time() * 1000 - start_time) < timeout_ms:
                try:
                    # 락 파일이 없으면 생성하고 성공
                    if not os.path.exists(lock_file):
                        with open(lock_file, 'w') as f:
                            f.write(str(os.getpid()))
                        # self._log("Server lock acquired")
                        return lock_file
                    
                    # 기존 락 파일이 있으면 잠시 대기
                    time.sleep(0.02)
                except:
                    time.sleep(0.02)
            
            # self._log("Server lock timeout")
            return None
        except Exception as e:
            self._log(f"Lock acquire error: {e}")
            return None

    def release_server_lock(self, lock_file):
        """파일 기반 락 해제"""
        try:
            if lock_file and os.path.exists(lock_file):
                os.remove(lock_file)
                # self._log("Server lock released")
        except Exception as e:
            self._log(f"Lock release error: {e}")
            

    def regist(self, callback, callback_name):
        self.callbacks[callback_name] = callback
        # self._log(f"Registered callback: {callback_name}")
    
    def _generate_id(self, length=16):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def request(self, callback_name, params=None, ignore_response = False):
        if params is None:
            params = []
        request_id = self._generate_id(16)

        text = f"RPC|{request_id}|{callback_name}|{int(ignore_response)}"
        for p in params:
            text += f"|{p}"
        
        # self._log(f"Sending request: {text}")
        
        # 큐에 추가
        success = False
        for attempt in range(10):
            try:
                with open(self.request_queue, 'a', encoding=self.ENCODING, newline='') as f:
                    f.write(text + '\n')  # \n으로 통일
                    f.flush()
                    os.fsync(f.fileno()) 
                success = True
                break
            except Exception as e:
                time.sleep(0.01)
        
        if not success:
            # self._log("Failed to write to queue after 10 attempts")
            return 1

        # 응답 대기
        if(not ignore_response):
            res_completed = os.path.join(self.communication_path, f"rpc_res_COMPLETED_{request_id}.txt")
            res_fail = os.path.join(self.communication_path, f"rpc_res_FAIL_{request_id}.txt")
            for i in range(50):
                if os.path.exists(res_completed):
                    try:
                        with open(res_completed, 'r', encoding=self.ENCODING) as f:
                            result = f.read()
                        os.remove(res_completed)
                        try:
                            os.remove(res_fail)
                        except:
                            pass
                        # self._log(f"Got response: {result}")
                        return result
                    except Exception as e:
                        self._log(f"Response read error: {e}")
                
                time.sleep(0.1)

            if os.path.exists(res_fail):
                try:
                    with open(res_fail, 'r', encoding=self.ENCODING) as f:
                        result = f.read()
                    os.remove(res_fail)
                    # self._log(f"Got fail response: {result}")
                    return 1
                except:
                    pass
            
            # self._log("Request timeout")
            return 1
    
    def spin(self):
        self.running = True
        # self._log("Starting check thread")
        thread = threading.Thread(target=self._check, daemon=True)
        thread.start()
    
    def _check(self):
        # self._log("Check thread started")
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                if check_count % 100 == 0:  # 10초마다 로그
                    self._log(f"Check cycle {check_count}, callbacks: {list(self.callbacks.keys())}")
                
                if not os.path.exists(self.request_queue):
                    time.sleep(0.1)
                    continue
                
                # 서버 락 획득
                server_lock = self.acquire_server_lock(1000)
                if not server_lock:
                    time.sleep(0.1)
                    continue

                try:
                    # 큐 파일 읽기
                    try:
                        with open(self.request_queue, 'r', encoding=self.ENCODING) as f:
                            text = f.read()
                        
                        if text.strip():  # 큐에 내용이 있으면 로그
                            self._log(f"Queue content: {repr(text)}")
                            
                    except Exception as e:
                        self._log(f"Queue read error: {e}")
                        continue

                    lines = text.split('\n')
                    processed = False
                    new_lines = []
                    request_id, name, params = "", "", []

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # self._log(f"Processing line: {line}")
                        
                        if not line.startswith("RPC|"):
                            # self._log(f"Skipping non-RPC line: {line}")
                            continue

                        if not processed:
                            parts = line.split("|")
                            if len(parts) < 4:
                                # self._log(f"Invalid RPC format: {line}")
                                continue
                            
                            request_id = parts[1]
                            name = parts[2]
                            ignore_response = int(parts[3])
                            # self._log(f"Found RPC request - ID: {request_id}, Name: {name}")

                            # FAIL 파일 미리 생성
                            if(not ignore_response):
                                res_fail = os.path.join(self.communication_path, f"rpc_res_FAIL_{request_id}.txt")
                                try:
                                    with open(res_fail, 'w', encoding=self.ENCODING) as f:
                                        f.write("srv_may_be_ended")
                                except:
                                    pass

                            if name in self.callbacks:
                                params = []
                                for val in parts[4:]:
                                    try:
                                        if '.' in str(val):
                                            params.append(float(val))
                                        else:
                                            params.append(int(val))
                                    except:
                                        params.append(val)
                                
                                processed = True
                                # self._log(f"Will process callback {name} with params: {params}")
                                continue  # 이 줄은 큐에서 제거
                            else:
                                # self._log(f"No callback for {name}")
                                new_lines.append(line)
                                continue
                        
                        new_lines.append(line)

                    # 큐 업데이트
                    try:
                        with open(self.request_queue, 'w', encoding=self.ENCODING) as f:
                            for l in new_lines:
                                if l.strip():
                                    f.write(l + '\n')
                        
                        # if processed:
                        #     self._log(f"Queue updated, removed processed item")
                            
                    except Exception as e:
                        self._log(f"Queue update error: {e}")

                except Exception as e:
                    self._log(f"Check processing error: {e}")
                finally:
                    self.release_server_lock(server_lock)

                # 콜백 처리
                if processed:
                    # self._log(f"Executing callback {name}")
                    try:
                        cb = self.callbacks[name]
                        
                        if len(params) == 0:
                            result = cb()
                        elif len(params) == 1:
                            result = cb(params[0])
                        elif len(params) == 2:
                            result = cb(params[0], params[1])
                        else:
                            result = cb(*params)

                        if(not ignore_response):
                            res_completed = os.path.join(self.communication_path, f"rpc_res_COMPLETED_{request_id}.txt")
                            res_fail = os.path.join(self.communication_path, f"rpc_res_FAIL_{request_id}.txt")

                            # 기존 파일들 삭제
                            try:
                                os.remove(res_fail)
                            except:
                                pass
                            try:
                                os.remove(res_completed)
                            except:
                                pass
                            
                            # 결과 파일 생성
                            with open(res_completed, 'w', encoding=self.ENCODING) as f:
                                f.write(str(result))
                            
                            # self._log(f"Callback result: {result}")

                    except Exception as e:
                        self._log(f"Callback execution error: {e}")
                        
            except Exception as e:
                self._log(f"Main check error: {e}")
            
            time.sleep(0.1)