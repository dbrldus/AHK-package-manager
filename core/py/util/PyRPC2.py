# PyRPC.py - Queue-based RPC
import os
import time
import threading
import random
import string

class RPCManager:
    def __init__(self, _temp_path: str):
        self.callbacks = {}
        self.running = False
        self.temp_path = _temp_path
        self.request_queue = os.path.join(self.temp_path, "rpc_requests.queue")
        self.response_dir = self.temp_path

        if not os.path.exists(self.request_queue):
            with open(self.request_queue, 'w') as f:
                pass
        
    def regist(self, callback, callback_name):
        self.callbacks[callback_name] = callback
    
    def _generate_id(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    def request(self, callback_name, params=None):
        if params is None:
            params = []
        request_id = self._generate_id()

        text = f"RPC|{request_id}|{callback_name}"
        for p in params:
            text += f"|{p}"
        for _ in range(10):
            try:
                with open(self.request_queue, 'a', encoding='utf-8') as f:
                    f.write(text + '\n')
                break
            except Exception as e:
                time.sleep(0.001)
        else:
            return ""
        res = os.path.join(self.response_dir, f"rpc_res_{request_id}.txt")
        
        for _ in range(50):
            if os.path.exists(res):
                try:
                    with open(res, 'r') as f:
                        result = f.read()
                    os.remove(res)
                    
                    try:
                        if '.' in result:
                            return float(result)
                        return int(result)
                    except:
                        return result
                except:
                    pass
            
            time.sleep(0.1)
        
        return ""
    
    def spin(self):
        self.running = True
        thread = threading.Thread(target=self._check, daemon=True)
        thread.start()
        print("now spinning")
    
    def _check(self):
        while self.running:
            try:
                if not os.path.exists(self.request_queue):
                    with open(self.request_queue, 'w') as f:
                        pass
                    time.sleep(0.1)
                    continue
                
                lines_to_process = []
                remaining_lines = []
                
                try:
                    with open(self.request_queue, 'r') as f:
                        all_lines = f.readlines()
                except:
                    time.sleep(0.1)
                    continue
                
                found = False
                for line in all_lines:
                    line = line.strip()
                    if not line:
                        continue
                    if not found and line.startswith("RPC|"):
                        lines_to_process.append(line)
                        found = True
                    else:
                        remaining_lines.append(line)
                
                if lines_to_process:
                    try:
                        with open(self.request_queue, 'w') as f:
                            for line in remaining_lines:
                                f.write(line + '\n')
                    except:
                        pass
                    
                    # 요청 처리
                    for line in lines_to_process:
                        parts = line.split("|")
                        if len(parts) < 3:
                            continue
                        
                        request_id = parts[1]
                        name = parts[2]
                        
                        res = os.path.join(self.response_dir, f"rpc_res_{request_id}.txt")
                        
                        if name not in self.callbacks:
                            with open(res, 'w') as f:
                                f.write("ERROR")
                            continue
                        
                        params = []
                        for val in parts[3:]:
                            try:
                                if '.' in val:
                                    params.append(float(val))
                                else:
                                    params.append(int(val))
                            except:
                                params.append(val)
                        
                        try:
                            result = self.callbacks[name](*params)
                            with open(res, 'w') as f:
                                f.write(str(result))
                        except Exception as e:
                            print(f"RPC Error: {e}")
                            with open(res, 'w') as f:
                                f.write("ERROR")
                
            except Exception as e:
                print(f"RPC Check Error: {e}")
                pass
            
            time.sleep(0.1)
