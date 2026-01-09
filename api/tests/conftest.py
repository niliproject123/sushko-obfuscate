import sys
from pathlib import Path

# Add project root to path for imports
# tests is now under api/, so go up two levels
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
