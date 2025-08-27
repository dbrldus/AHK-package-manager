import os, json

def find_project_root(start_path=None):
    if start_path is None:
        start_path = os.path.dirname(__file__)
    cur = os.path.abspath(start_path)
    while True:
        anchor = os.path.join(cur, ".ANCHOR")
        if os.path.exists(anchor):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return None

ROOT_PATH = find_project_root()
CORE_PATH = os.path.join(ROOT_PATH, "core")
DATA_PATH = os.path.join(ROOT_PATH, "data")
CONFIG_PATH = os.path.join(ROOT_PATH, "config")
RUNTIME_PATH = os.path.join(CORE_PATH, "runtime")
SCHEMA_PATH = os.path.join(CORE_PATH, "schema")
TEMP_PATH = os.path.join(CORE_PATH, "tmp")
ASSETS_PATH = os.path.join(ROOT_PATH, "assets")
ICONS_PATH = os.path.join(ASSETS_PATH, "icons")
PKGS_PATH = os.path.join(ROOT_PATH, "packages")
MAIN_IPC_PATH = os.path.join(TEMP_PATH, "ipc")
os.makedirs(MAIN_IPC_PATH, exist_ok=True)


# RUNTIME_PATH는 문자열 경로라고 가정
os.makedirs(RUNTIME_PATH, exist_ok=True)

# 1. package-status.json (기본 [])
package_status_path = os.path.join(RUNTIME_PATH, "package-status.json")
if not os.path.exists(package_status_path):
    with open(package_status_path, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)

# 2. hub-status.json (기본 {"is_active": "False", "PID": -1})
hub_status_path = os.path.join(RUNTIME_PATH, "hub-status.json")
if not os.path.exists(hub_status_path):
    default_hub = {"is_active": "False", "PID": -1}
    with open(hub_status_path, "w", encoding="utf-8") as f:
        json.dump(default_hub, f, ensure_ascii=False)