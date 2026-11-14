from config.settings.test import *
from pathlib import Path
ROOT=Path("/private/tmp/sukoon-sprint10")
DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":str(ROOT/"unused.sqlite3"),"TEST":{"NAME":":memory:"}}}
MEDIA_ROOT=str(ROOT/"media_root")
STATIC_ROOT=str(ROOT/"static_root")
CHAT_PRIVATE_MEDIA_ROOT=str(ROOT/"chat_private_media_root")
SUPPORT_PRIVATE_MEDIA_ROOT=str(ROOT/"support_private_media_root")
VIRTUAL_TOUR_PRIVATE_ROOT=str(ROOT/"virtual_tour_private_root")
EVIDENCE_PRIVATE_ROOT=str(ROOT/"evidence_private_root")
