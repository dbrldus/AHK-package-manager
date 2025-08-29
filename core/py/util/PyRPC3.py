import os
import socket
import threading
import random
import string
import time
import glob
import psutil
from datetime import datetime

class RPCManager:
    def __init__(self, namespace="default"):
        self.namespace = namespace
        self.callbacks = {}
        self.running = False
        self.process_id = os.getpid()
        self.services_dir = os.path.join(os.environ.get('TEMP', '/tmp'), f"rpc_services_{namespace}")
        self.tcp_servers = {}  # service_name -> {'port': port, 'server': server, 'thread': thread}
        
        # 서비스 디렉토리 생성
        os.makedirs(self.services_dir, exist_ok=True)
    
    def regist(self, callback, service_name):
        """서비스 등록"""
        self.callbacks[service_name] = callback
        
        # 사용 가능한 포트 찾기
        port = self.find_available_port(9000, 9999)
        if not port:
            raise Exception("사용 가능한 포트를 찾을 수 없습니다")
        
        # TCP 서버 시작
        server_socket = self.start_tcp_server(port, service_name)
        if not server_socket:
            raise Exception(f"TCP 서버 시작 실패: {service_name}")
        
        self.tcp_servers[service_name] = {
            'port': port, 
            'server': server_socket,
            'thread': None
        }
        
        # 서비스 파일 등록 (디스커버리용)
        service_file = os.path.join(self.services_dir, f"{service_name}_proc{self.process_id}_port{port}.service")
        try:
            with open(service_file, 'w') as f:
                f.write(f"{self.process_id}|{port}|{datetime.now().strftime('%Y%m%d%H%M%S')}")
        except Exception as e:
            raise Exception(f"서비스 등록 실패: {service_name} - {e}")
        
        return True
    
    def request(self, service_name, params=None, timeout_ms=5000):
        """서비스 요청"""
        if params is None:
            params = []
            
        # 서비스 디스커버리
        servers = self.discover_service(service_name)
        if not servers:
            return f"ERROR: 서비스를 찾을 수 없음 - {service_name}"
        
        # 랜덤 서버 선택 (로드 밸런싱)
        server = random.choice(servers)
        
        # TCP 연결 및 요청
        return self.send_tcp_request(server['host'], server['port'], service_name, params, timeout_ms / 1000.0)
    
    def discover_service(self, service_name):
        """서비스 디스커버리 (파일 스캔)"""
        servers = []
        pattern = os.path.join(self.services_dir, f"{service_name}_proc*_port*.service")
        
        for service_file in glob.glob(pattern):
            try:
                with open(service_file, 'r') as f:
                    content = f.read()
                
                parts = content.split('|')
                if len(parts) >= 2:
                    proc_id = int(parts[0])
                    port = int(parts[1])
                    
                    # 프로세스가 살아있는지 확인
                    if psutil.pid_exists(proc_id):
                        servers.append({
                            'host': '127.0.0.1',
                            'port': port,
                            'process_id': proc_id,
                            'file': service_file
                        })
                    else:
                        # 죽은 프로세스의 서비스 파일 삭제
                        try:
                            os.remove(service_file)
                        except:
                            pass
            except Exception as e:
                # 손상된 서비스 파일 삭제
                try:
                    os.remove(service_file)
                except:
                    pass
        
        return servers
    
    def find_available_port(self, start_port, end_port):
        """사용 가능한 포트 찾기"""
        for port in range(start_port, end_port + 1):
            if self.is_port_available(port):
                return port
        return None
    
    def is_port_available(self, port):
        """포트 사용 가능 여부 확인"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    def start_tcp_server(self, port, service_name):
        """TCP 서버 시작"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', port))
            server_socket.listen(10)
            server_socket.settimeout(0.1)  # non-blocking accept를 위한 타임아웃
            
            return server_socket
            
        except Exception as e:
            return None
    
    def send_tcp_request(self, host, port, service_name, params, timeout_seconds):
        """TCP 요청 전송"""
        try:
            # 클라이언트 소켓 생성
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(timeout_seconds)
            
            # 서버 연결
            client_socket.connect((host, port))
            
            # 요청 데이터 구성
            request_id = self._generate_id(16)
            request_data = f"REQ|{request_id}|{service_name}"
            for p in params:
                request_data += f"|{p}"
            
            # 데이터 전송
            client_socket.send(request_data.encode('utf-8'))
            
            # 응답 수신
            response = client_socket.recv(4096).decode('utf-8')
            client_socket.close()
            
            return response
            
        except socket.timeout:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {e}"
    
    def spin(self):
        """서버 시작"""
        self.running = True
        
        # 각 서비스별 TCP 서버 수신 스레드 시작
        for service_name, server_info in self.tcp_servers.items():
            thread = threading.Thread(
                target=self.accept_connections, 
                args=(service_name,), 
                daemon=True
            )
            thread.start()
            server_info['thread'] = thread
        
        # 정리 스레드 시작
        cleanup_thread = threading.Thread(target=self.cleanup_dead_services, daemon=True)
        cleanup_thread.start()
    
    def accept_connections(self, service_name):
        """연결 수락 및 처리"""
        if service_name not in self.tcp_servers:
            return
            
        server_socket = self.tcp_servers[service_name]['server']
        
        while self.running:
            try:
                client_socket, addr = server_socket.accept()
                
                # 요청 처리
                response = self.process_tcp_request(client_socket, service_name)
                
                # 응답 전송
                if response:
                    client_socket.send(response.encode('utf-8'))
                
                client_socket.close()
                
            except socket.timeout:
                continue  # non-blocking이라 타임아웃은 정상
            except Exception as e:
                pass  # 연결 오류는 무시
    
    def process_tcp_request(self, client_socket, service_name):
        """TCP 요청 처리"""
        try:
            # 데이터 수신
            data = client_socket.recv(4096).decode('utf-8')
            parts = data.split('|')
            
            if len(parts) < 3 or parts[0] != "REQ":
                return "ERROR: 잘못된 요청 형식"
            
            request_id = parts[1]
            received_service = parts[2]
            params = []
            
            # 파라미터 추출
            for val in parts[3:]:
                try:
                    if '.' in str(val):
                        params.append(float(val))
                    else:
                        params.append(int(val))
                except:
                    params.append(val)
            
            # 콜백 실행
            if service_name not in self.callbacks:
                return f"ERROR: 서비스가 등록되지 않음 - {service_name}"
            
            cb = self.callbacks[service_name]
            if len(params) == 0:
                result = cb()
            elif len(params) == 1:
                result = cb(params[0])
            elif len(params) == 2:
                result = cb(params[0], params[1])
            else:
                result = cb(*params)
            
            return str(result)
            
        except Exception as e:
            return f"ERROR: {e}"
    
    def cleanup_dead_services(self):
        """죽은 서비스 정리"""
        while self.running:
            try:
                pattern = os.path.join(self.services_dir, "*.service")
                for service_file in glob.glob(pattern):
                    try:
                        with open(service_file, 'r') as f:
                            content = f.read()
                        
                        parts = content.split('|')
                        if len(parts) >= 1:
                            proc_id = int(parts[0])
                            if not psutil.pid_exists(proc_id):
                                os.remove(service_file)
                    except:
                        # 손상된 파일 삭제
                        try:
                            os.remove(service_file)
                        except:
                            pass
            except:
                pass
            
            time.sleep(10)  # 10초마다 정리
    
    def _generate_id(self, length=16):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return ''.join(random.choice(chars) for _ in range(length))