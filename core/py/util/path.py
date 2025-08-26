import os

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