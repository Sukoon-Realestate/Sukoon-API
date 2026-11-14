"""Only this task's newly created Unix-socket cluster; no configurable target."""
import hashlib,json,os,subprocess,time
from pathlib import Path
import psycopg2
from psycopg2 import sql
ROOT=Path('/private/tmp/sukoon-sprint12')
EVIDENCE=Path('/Users/demo23home/code/sukoon/Sukoon-API/backend/sprints/evidence/sprint-12')
PG=Path('/opt/homebrew/opt/postgresql@18/bin')
ARGS=['-h',str(ROOT/'pg/socket'),'-p','55452','-U','sprint12']
SOURCE='test_sokoun_sprint12_operations'
RESTORE='test_sokoun_sprint12_restore'
assert (ROOT/'pg/data/PG_VERSION').read_text().strip()=='18'
os.environ['DOTENV_DISABLED']='1'
os.environ['DJANGO_SETTINGS_MODULE']='sprint12_operations'
import django
django.setup()
from core_apps.users.models import User
User.objects.create_user(email='sprint12-backup@example.invalid',password='DisposableBackupOnly12!',is_active=True,is_verified=True)
from django.db import connections
connections.close_all()

def snapshot(database):
    result={}
    conn=psycopg2.connect(host=str(ROOT/'pg/socket'),port=55452,user='sprint12',dbname=database)
    with conn,conn.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        tables=[r[0] for r in cur.fetchall()]
        for table in tables:
            cur.execute(sql.SQL('SELECT COUNT(*), COALESCE(jsonb_agg(x ORDER BY x)::text,\'[]\') FROM (SELECT to_jsonb(t) x FROM {} t) rows').format(sql.Identifier(table)))
            count,contents=cur.fetchone()
            result[table]={'rows':count,'content_sha256':hashlib.sha256(contents.encode()).hexdigest()}
        cur.execute('SELECT sequencename, last_value FROM pg_sequences WHERE schemaname=\'public\' ORDER BY sequencename')
        sequences=cur.fetchall()
    conn.close()
    return {'tables':result,'sequences':sequences}
start=time.monotonic()
before=snapshot(SOURCE)
dump=ROOT/'operations.dump'
subprocess.run([str(PG/'pg_dump'),*ARGS,'-Fc','-f',str(dump),SOURCE],check=True)
subprocess.run([str(PG/'createdb'),*ARGS,RESTORE],check=True)
subprocess.run([str(PG/'pg_restore'),*ARGS,'--exit-on-error','--dbname',RESTORE,str(dump)],check=True)
after=snapshot(RESTORE)
report={'source':SOURCE,'restore':RESTORE,'cluster':'new task-owned PostgreSQL 18; private Unix socket; TCP disabled','table_count':len(before['tables']),'all_table_contents_equal':before['tables']==after['tables'],'sequences_equal':before['sequences']==after['sequences'],'dump_sha256':hashlib.sha256(dump.read_bytes()).hexdigest(),'dump_bytes':dump.stat().st_size,'elapsed_seconds':round(time.monotonic()-start,3),'table_evidence':before['tables'],'limits':'Synthetic local database restore only. No real media/config/secrets backup or production RPO/RTO acceptance.'}
(EVIDENCE/'backup-restore.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['all_table_contents_equal'] and report['sequences_equal']
print(json.dumps({k:v for k,v in report.items() if k!='table_evidence'}))
