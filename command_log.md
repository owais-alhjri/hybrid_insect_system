# Command Log

- `ls`
- `find .. -name AGENTS.md -print`
- `python - <<'PY'
from pathlib import Path
p=Path('README.md').read_bytes()
print(p[:200])
PY`
- `python - <<'PY'
from pathlib import Path
text=Path('README.md').read_text(encoding='utf-16')
print(text)
PY`
- `rg -n "tello|drone|tank|yahboom|cooperative|detect|verify|report|insect" -S .`
- `sed -n '1,200p' main.py`
- `sed -n '1,200p' controller/coordinator.py`
- `sed -n '1,200p' mock/mock_drone.py`
- `sed -n '1,200p' mock/mock_tank.py`
- `sed -n '1,200p' ai/detector.py`
- `sed -n '1,200p' run_demo.py`
- `sed -n '1,200p' backend/api.py`
- `sed -n '1,200p' backend/database.py`
- `sed -n '1,200p' notes.txt`
- `sed -n '1,200p' config.py`
