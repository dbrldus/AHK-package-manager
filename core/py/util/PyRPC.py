import os
import time
import tempfile
import threading

class RPCManager:
    def __init__(self, _temp_path: str):
        self.callbacks = {}
        self.running = False
        self.temp_path = _temp_path
        
    def regist(self, callback, callback_name):
        self.callbacks[callback_name] = callback
    
    def request(self, callback_name, params=None):
        if params is None:
            params = []
        req = os.path.join(self.temp_path, f"rpc_req_{callback_name}.txt")  # 변경함
        res = os.path.join(self.temp_path, f"rpc_res_{callback_name}.txt")  # 변경함
        try:
            if os.path.exists(res):
                os.remove(res)
        except:
            pass
        
        text = f"AHK|{callback_name}"
        for p in params:
            text += f"|{p}"
        
        with open(req, 'w') as f:
            f.write(text)
        
        # Wait for response
        for _ in range(50):
            if os.path.exists(res):
                with open(res, 'r') as f:
                    result = f.read()
                
                # Clean up files
                if os.path.exists(res):
                    os.remove(res)
                if os.path.exists(req):
                    os.remove(req)
                
                # Convert to number if possible
                try:
                    if '.' in result:
                        return float(result)
                    return int(result)
                except:
                    return result
            
            time.sleep(0.1)
        
        if os.path.exists(req):
            os.remove(req)
        return ""
    
    def spin(self):
        self.running = True
        
        thread = threading.Thread(target=self._check, daemon=True)
        thread.start()
    
    def _check(self):
        while self.running:
            try:
                for name in os.listdir(self.temp_path):
                    if not (name.startswith("rpc_req_") and name.endswith(".txt")):
                        continue
                    req = os.path.join(self.temp_path, name)
                    res = os.path.join(self.temp_path, name.replace("rpc_req_", "rpc_res_", 1))
                    try:
                        with open(req, 'r') as f:
                            text = f.read()
                    except:
                        continue

                    if not text.startswith("PY|"):
                        continue

                    try:
                        os.remove(req)
                    except:
                        pass

                    parts = text.split("|")
                    if len(parts) < 2:
                        continue

                    name_ = parts[1]
                    if name_ not in self.callbacks:
                        with open(res, 'w') as f:
                            f.write("ERROR")
                        continue

                    params = []
                    for val in parts[2:]:
                        try:
                            params.append(float(val) if '.' in val else int(val))
                        except:
                            params.append(val)

                    try:
                        result = self.callbacks[name_](*params)
                        with open(res, 'w') as f:
                            f.write(str(result))
                    except:
                        with open(res, 'w') as f:
                            f.write("ERROR")
                    break
            except:
                pass
            
            time.sleep(0.1)