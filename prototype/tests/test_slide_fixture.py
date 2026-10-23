import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import export_slide_fixture  # noqa: E402


def test_frontend_slide_fixture_is_up_to_date():
    # If this fails, keyboard.py's cleanup changed: run `python export_slide_fixture.py`
    # and then `npm test` in frontend/ to check the TypeScript copy still agrees.
    assert export_slide_fixture.FIXTURE.read_text(encoding="utf-8") == export_slide_fixture.render()
