"""Root conftest: add src/ to sys.path so tests can import yad2_car_bot without installing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
