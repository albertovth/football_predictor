from pathlib import Path
from runpy import run_path


APP_ENTRYPOINT = Path(__file__).resolve().parent / "app" / "football_predictor.py"


run_path(str(APP_ENTRYPOINT), run_name="__main__")
