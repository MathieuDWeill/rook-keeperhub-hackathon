import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from apps.api.app.main import app

out = Path("artifacts/openapi.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(out)
