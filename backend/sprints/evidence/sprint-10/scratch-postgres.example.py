from sprint10_sqlite import *
import os
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'postgres','USER':'sprint10','HOST':'/private/tmp/sukoon-sprint10/pg/socket','PORT':'55450','TEST':{'NAME':os.environ.get('SPRINT10_TEST_DB','test_sprint10_focused'),'CHARSET':'UTF8','TEMPLATE':'template0'}}}
