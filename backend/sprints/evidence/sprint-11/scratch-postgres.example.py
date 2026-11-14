from sprint11_sqlite import *
import os
DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":"postgres","USER":"sprint11","HOST":"/private/tmp/sukoon-sprint11/pg/socket","PORT":"55451","TEST":{"NAME":os.environ.get("SPRINT11_TEST_DB","test_sprint11_scoped"),"CHARSET":"UTF8","TEMPLATE":"template0"}}}
