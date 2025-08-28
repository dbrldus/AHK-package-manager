import os
import time
import threading
import random
import string
import ctypes
from ctypes import wintypes
from datetime import datetime

def file_auto_gen(filepath):
    if os.path.exists(filepath):
        return True
    
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            pass
        
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
        self.debug_file = os.path.join(self.communication_path, "python_debug.log")
        self.duplicate_window = 2
        self.server_lock_handle = None 
        # 중복 감지 시스템 - dict로 O(1) 조회
        
        file_auto_gen(self.request_queue)

    def _log(self, message):
        """디버깅용 로그"""
        try:
            with open(self.debug_file, 'a', encoding=self.ENCODING) as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")
            print(f"[PYTHON] {message}")
        except:
            pass

    def acquire_server_lock(self, timeout_ms=1000):
        lock_file = os.path.join(self.communication_path, "rpc_server.lock")
        start_time = time.time() * 1000
        
        while (time.time() * 1000 - start_time) < timeout_ms:
            try:
                # 배타적으로 파일 열기
                handle = open(lock_file, 'w', encoding=self.ENCODING)
                handle.write(str(os.getpid()))
                handle.flush()
                return handle  # 핸들 반환 (파일 열린 상태 유지)
            except (IOError, OSError):
                time.sleep(0.02)
        
        return None

    def release_server_lock(self, handle):
        if handle:
            try:
                handle.close()  # 파일 닫으면 자동 락 해제
            except:
                pass
    
    def cleanup_processed_requests(self):
        """오래된 처리 기록 정리"""
        processed_file = os.path.join(self.communication_path, "processed_requests.txt")
        if not os.path.exists(processed_file):
            return
        
        try:
            # 파일 크기 확인 - 10KB 미만이면 건너뛰기
            if os.path.getsize(processed_file) < 10240:
                return
            
            with open(processed_file, 'r', encoding=self.ENCODING) as f:
                content = f.read()
            
            lines = content.split('\n')
            new_lines = []
            current_time = self.get_timestamp()
            removed_count = 0
            
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split('|')
                if len(parts) >= 2:
                    time_diff = self.get_time_difference_seconds(parts[1], current_time)
                    if time_diff <= self.duplicate_window:
                        new_lines.append(line)
                    else:
                        removed_count += 1
            
            # 정리할 게 있으면 파일 업데이트
            if removed_count > 0:
                with open(processed_file, 'w', encoding=self.ENCODING) as f:
                    for line in new_lines:
                        f.write(line + '\n')
                        
        except Exception as e:
            self._log(f"Cleanup error: {e}")
    
    def record_processed_request(self, request_id, timestamp):

        processed_file = os.path.join(self.communication_path, "processed_requests.txt")
        try:
            with open(processed_file, 'a', encoding=self.ENCODING) as f:
                f.write(f"{request_id}|{timestamp}\n")
        except:
            pass
    
    
    def _process_exists(self, pid):
        """프로세스 존재 확인"""
        try:
            import psutil
            return psutil.pid_exists(pid)
        except:
            # psutil 없으면 간단한 방법
            try:
                os.kill(pid, 0)
                return True
            except:
                return False
    
    def regist(self, callback, callback_name):
        self.callbacks[callback_name] = callback
    
    def _generate_id(self, length=16):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def get_timestamp(self):
        """YYYYMMDDHHMISS 형식 타임스탬프 생성"""
        return datetime.now().strftime("%Y%m%d%H%M%S")
    
    def get_time_difference_seconds(self, time1, time2):
        """두 타임스탬프 간의 차이를 초로 계산"""
        try:
            dt1 = datetime.strptime(time1, "%Y%m%d%H%M%S")
            dt2 = datetime.strptime(time2, "%Y%m%d%H%M%S")
            return abs((dt2 - dt1).total_seconds())
        except:
            return float('inf')  # 파싱 오류 시 큰 값 반환
    
    def cleanup_recent_requests(self, current_timestamp):
        """dict에서 오래된 요청들 제거"""
        keys_to_remove = []
        
        for request_id, timestamp in self.recent_requests.items():
            time_diff = self.get_time_difference_seconds(timestamp, current_timestamp)
            if time_diff > self.duplicate_window:
                keys_to_remove.append(request_id)
        
        for key in keys_to_remove:
            del self.recent_requests[key]
    
    def is_duplicate_request(self, request_id, timestamp):
        processed_file = os.path.join(self.communication_path, "processed_requests.txt")
        
        if not os.path.exists(processed_file):
            return False
        
        try:
            with open(processed_file, 'r', encoding=self.ENCODING) as f:
                content = f.read()
            
            lines = content.split('\n')
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split('|')
                if len(parts) >= 2 and parts[0] == request_id:
                    time_diff = self.get_time_difference_seconds(parts[1], timestamp)
                    if time_diff <= self.duplicate_window:
                        return True
        except:
            pass
        
        return False
    
    def request(self, callback_name, params=None, ignore_response=False):
        if params is None:
            params = []
        
        request_id = self._generate_id(16)
        timestamp = self.get_timestamp()
        
        # 새로운 형식: RPC|ID|NAME|IGNORE|TIMESTAMP|PARAMS...
        text = f"RPC|{request_id}|{callback_name}|{int(ignore_response)}|{timestamp}"
        for p in params:
            text += f"|{p}"
        
        # 큐에 추가
        success = False
        for attempt in range(10):
            try:
                with open(self.request_queue, 'a', encoding=self.ENCODING, newline='') as f:
                    f.write(text + '\n')
                    f.flush()
                    os.fsync(f.fileno()) 
                success = True
                break
            except Exception as e:
                self._log(f"Write error (attempt {attempt}): {e}")
                time.sleep(0.01)
        
        if not success:
            return 1

        # 응답 대기
        if not ignore_response:
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
                        return result
                    except Exception as e:
                        self._log(f"Response read error: {e}")
                
                time.sleep(0.1)

            if os.path.exists(res_fail):
                try:
                    with open(res_fail, 'r', encoding=self.ENCODING) as f:
                        result = f.read()
                    os.remove(res_fail)
                    return 1
                except:
                    pass
            
            return 1
        return 0
    
    def spin(self):
        self.running = True
        thread = threading.Thread(target=self._check, daemon=True)
        thread.start()
    
    def _check(self):
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                if check_count % 100 == 0:
                    self._log(f"Check cycle {check_count}, callbacks: {list(self.callbacks.keys())}")
                
                if not os.path.exists(self.request_queue):
                    time.sleep(0.1)
                    continue
                
                
                current_time = time.time()
                if not hasattr(self, 'last_cleanup'):
                    self.last_cleanup = time.time()
                current_time = time.time()
                if current_time - self.last_cleanup > 30:
                    self.cleanup_processed_requests()
                    self.last_cleanup = current_time
                
                server_lock = self.acquire_server_lock(1000)
                if not server_lock:
                    time.sleep(0.1)
                    continue

                try:
                    # 큐 파일 읽기
                    try:
                        with open(self.request_queue, 'r', encoding=self.ENCODING) as f:
                            text = f.read()
                        
                        if text.strip():
                            self._log(f"Queue content: {repr(text)}")
                            
                    except Exception as e:
                        self._log(f"Queue read error: {e}")
                        continue

                    lines = text.split('\n')
                    new_lines = []
                    request_to_process = ""
                    callback_name = ""
                    callback_params = []
                    ignore_response = False

                    for line in lines:
                        line = line.strip()

                        if not line:
                            continue
                        if not line.startswith("RPC|"):
                            # 더미 문자열은 로그 후 제거 (보존하지 않음)
                            # self._log(f"Invalid queue line removed: {line}")
                            continue

                        parts = line.split("|")
                        if len(parts) < 5:  # 최소 RPC|ID|NAME|IGNORE|TIMESTAMP
                            continue
                        
                        request_id = parts[1]
                        name = parts[2]
                        ignore_resp = int(parts[3])
                        timestamp = parts[4]
                        
                        # 중복 요청 검사
                        if self.is_duplicate_request(request_id, timestamp):
                            # 중복 발견 - 큐에서 제거하고 무시
                            self._log(f"Duplicate request ignored: {request_id}")
                            continue
                        
                        # 유효한 콜백이 있고 아직 처리할 요청이 없는 경우
                        if request_to_process == "" and name in self.callbacks:
                            request_to_process = request_id
                            callback_name = name
                            ignore_response = ignore_resp
                            
                            # 파라미터 추출 (timestamp 이후)
                            callback_params = []
                            for val in parts[5:]:
                                try:
                                    if '.' in str(val):
                                        callback_params.append(float(val))
                                    else:
                                        callback_params.append(int(val))
                                except:
                                    callback_params.append(val)
                            
                            self.record_processed_request(request_id, timestamp)
                            
                            # FAIL 응답 파일 미리 생성
                            if not ignore_response:
                                res_fail = os.path.join(self.communication_path, f"rpc_res_FAIL_{request_id}.txt")
                                try:
                                    with open(res_fail, 'w', encoding=self.ENCODING) as f:
                                        f.write("srv_may_be_ended")
                                except:
                                    pass
                            
                            # 큐에서 제거
                            continue
                        
                        # 처리하지 않는 요청들은 큐에 보존
                        new_lines.append(line)

                    # 큐 업데이트
                    try:
                        with open(self.request_queue, 'w', encoding=self.ENCODING) as f:
                            for l in new_lines:
                                if l.strip():
                                    f.write(l + '\n')
                    except Exception as e:
                        self._log(f"Queue update error: {e}")

                except Exception as e:
                    self._log(f"Check processing error: {e}")
                finally:
                    self.release_server_lock(server_lock)

                # 콜백 처리
                if request_to_process:
                    self._execute_callback(request_to_process, callback_name, callback_params, ignore_response)
                        
            except Exception as e:
                self._log(f"Main check error: {e}")
            
            time.sleep(0.1)
    
    def _execute_callback(self, request_id, name, params, ignore_response):
        """콜백 실행을 별도 함수로 분리"""
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

            if not ignore_response:
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

        except Exception as e:
            self._log(f"Callback execution error: {e}")
            if not ignore_response:
                res_fail = os.path.join(self.communication_path, f"rpc_res_FAIL_{request_id}.txt")
                try:
                    os.remove(res_fail)
                except:
                    pass
                try:
                    with open(res_fail, 'w', encoding=self.ENCODING) as f:
                        f.write(f"ERROR: {str(e)}")
                except:
                    pass