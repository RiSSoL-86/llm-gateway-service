from pathlib import Path

import dmr
from django.conf import settings
from django.contrib.staticfiles import finders

SWAGGER_INIT = "dmr/swagger/init.js"
OURS = settings.BASE_DIR / "static" / SWAGGER_INIT
DMR = Path(dmr.__file__).parent / "static" / SWAGGER_INIT

# The only lines our Swagger start script adds to the DMR one
PLAIN_TEXT_ANSWERS = (
    "      // Coloring the 850 KB `/models` answer freezes the page:"
    " plain text\n"
    "      syntaxHighlight: false,\n"
)


def test_serves_own_swagger_init() -> None:
    assert Path(finders.find(path=SWAGGER_INIT)) == OURS


def test_swagger_init_is_dmr_one_with_plain_answers() -> None:
    ours = OURS.read_text(encoding="utf-8")

    assert PLAIN_TEXT_ANSWERS in ours
    # Fails on a DMR bump that changes its script: copy it again, add ours
    assert ours.replace(PLAIN_TEXT_ANSWERS, "") == DMR.read_text(
        encoding="utf-8"
    )
