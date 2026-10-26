from pathlib import Path
import json,re,hashlib
root=Path(__file__).resolve().parents[5];app=root/'sokoun/apps/sokoun_app/lib';out=root/'Sukoon-API/docs/design/mobile-identity-proposal/sprints'
rows=json.loads((out/'screen-inventory.json').read_text())['screens']
files={p:p.read_text() for p in app.rglob('*.dart')};classes={}
for p,t in files.items():
 for name in re.findall(r'(?:class|enum|mixin)\s+(\w+)',t):classes.setdefault(name,[]).append(p)
records=[]
for rec in sorted((r for r in rows if 11<=r.get('sprint',0)<=14),key=lambda r:int(r['proposalId'][1:])):
 p=root/rec['source'];text=files[p];deps=[]
 feature='/'.join(rec['source'].split('/lib/features/')[1].split('/')[:2])
 names=list(dict.fromkeys(re.findall(r'\b(_?[A-Z][A-Za-z0-9_]*)\b',text)))
 for name in names:
  for dep in classes.get(name,[]):
   if dep!=p and dep not in deps and (('/features/'+feature+'/') in str(dep) or re.search(r'(Guard|Recovery|Confirm|Draft|Capture)',name)):deps.append(dep)
 # Inspect feature-owned presentation children one layer deeper as well.
 for dep in list(deps):
  for name in list(dict.fromkeys(re.findall(r'\b(_?[A-Z][A-Za-z0-9_]*)\b',files[dep]))):
   for child in classes.get(name,[]):
    if child!=p and child not in deps and '/features/'+feature+'/' in str(child) and ('/widgets/' in str(child) or '/models/' in str(child)):deps.append(child)
 deps=deps[:30]
 texts=[text]+[files[d] for d in deps]
 def key(t):return sorted(set(re.findall(r'LocaleKeys\.(\w+)',t)))
 data={**rec,'dependencies':[{'source':str(d.relative_to(root)),'sha256':hashlib.sha256(files[d].encode()).hexdigest(),'localeKeys':key(files[d])} for d in deps], 'auditedLocaleKeys':sorted(set(k for t in texts for k in key(t))), 'guardAndStateExpressions':list(dict.fromkeys(re.findall(r'\bif\s*\(([^\n]{1,160})', '\n'.join(texts))))[:35], 'sourceCommands':list(dict.fromkeys(re.findall(r'(?:_cubit|cubit|_write|_read|source)\.([a-zA-Z]+)\(', '\n'.join(texts)))),'controllerFields':sorted(set(re.findall(r'\b(_[a-zA-Z]+)\s*=\s*TextEditingController','\n'.join(texts))))}
 records.append(data)
(out/'batch-11-14-source-audit.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print('Captured',len(records),'primary screens and',sum(len(x['dependencies']) for x in records),'dependency references')
