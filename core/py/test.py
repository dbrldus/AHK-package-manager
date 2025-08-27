from util.PyRPC2 import RPCManager
from util.path import *
import time

# 공통 경로 사용
rpc = RPCManager(os.path.join(TEMP_PATH, "ipc"))

rpc.request("ping",[],True)