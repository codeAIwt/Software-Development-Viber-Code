import sys, subprocess, os

# Ensure PyYAML installed
try:
    import yaml
except Exception:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"], stdout=subprocess.DEVNULL)
    import yaml

p = os.path.join(os.getcwd(), ".github", "workflows", "main.yml")
if not os.path.exists(p):
    print(f"ERROR: file not found: {p}")
    sys.exit(2)

try:
    with open(p, 'r', encoding='utf-8') as f:
        yaml.safe_load(f)
    print('YAML_OK')
    sys.exit(0)
except Exception as e:
    print('YAML_ERROR')
    import traceback
    traceback.print_exc()
    sys.exit(1)
