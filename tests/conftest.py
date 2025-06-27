from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path for helper imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
# Add src directory for observability imports
sys.path.insert(0, str(project_root / "src"))
