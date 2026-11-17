import json,sys,pathlib
import django
django.setup()
from django.db import connection,transaction,IntegrityError
from django.db.migrations.executor import MigrationExecutor
phase=sys.argv[1]
last='0016_alter_usersocialauth_extra_data' if phase=='before' else '0020_backfill_id_keys'
executor=MigrationExecutor(connection)
executor.migrate([('social_django',last)])
apps=executor.loader.project_state([('social_django',last)]).apps
Social=apps.get_model('social_django','UserSocialAuth')
User=apps.get_model('users','User')
if phase=='before':
 user=User.objects.create(email='upgrade-qa@example.test',password='!')
 for provider,uid in [('google-oauth2','upgrade-qa@example.test'),('apple-id','qa-apple-subject'),('facebook','qa-facebook-subject')]:
  Social.objects.create(user_id=user.pk,provider=provider,uid=uid,extra_data={'qa_only':True,'label':'سكون'})
rows=list(Social.objects.order_by('provider').values('id','user_id','provider','uid','extra_data'))
normalized=json.loads(json.dumps(rows,default=str))
p=pathlib.Path('/private/tmp/sprint1-20261117/social-before.json')
if phase=='before':p.write_text(json.dumps(normalized,ensure_ascii=False,indent=2))
else:
 assert normalized==json.loads(p.read_text()),'Existing association identity/data changed'
 keys=dict(Social.objects.values_list('provider','id_key'))
 assert keys=={'google-oauth2':'email','apple-id':'sub','facebook':'id'},keys
 try:
  with transaction.atomic():Social.objects.create(user_id=rows[0]['user_id'],provider='google-oauth2',uid='')
 except IntegrityError:pass
 else:raise AssertionError('Empty provider identity was accepted')
 print('PASS: three existing associations retained primary/user/provider IDs, UID and JSON; id_key backfills and empty-UID constraint verified')
print('migration target',last,'rows',len(rows))
