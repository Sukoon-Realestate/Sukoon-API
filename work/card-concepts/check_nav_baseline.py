from pathlib import Path
import subprocess
root=Path('/Users/demo23home/code/sukoon/sokoun')
app=root/'apps/sokoun_app'
baseline=app/'test/_navigation_baseline'
copy=app/'test/navigation_clearance_baseline_test.dart'
try:
 baseline.mkdir(exist_ok=True)
 for name in ['home_bottom_navigation.dart','home_navigation_item.dart','home_navigation_icon.dart']:
  content=subprocess.check_output(['git','show',f'HEAD:apps/sokoun_app/lib/features/main_view/presentation/widgets/{name}'],cwd=root,text=True)
  content=content.replace("'../models/home_navigation_destination.dart'", "'package:sokoun_app/features/main_view/presentation/models/home_navigation_destination.dart'")
  (baseline/name).write_text(content)
 content=(app/'test/workspace_navigation_clearance_test.dart').read_text().replace("'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart'", "'_navigation_baseline/home_bottom_navigation.dart'")
 copy.write_text(content)
 with Path('/tmp/navigation-baseline-check.txt').open('w') as log:
  result=subprocess.run(['flutter','test','--no-pub',str(copy.relative_to(app)),'--plain-name','last company saved lists action clears navigation ar large text'],cwd=app,stdout=log,stderr=subprocess.STDOUT)
 print('Baseline test exit:',result.returncode)
 for line in Path('/tmp/navigation-baseline-check.txt').read_text().splitlines():
  if 'finder ' in line or 'Company' in line or 'Some tests failed' in line: print(line)
finally:
 copy.unlink(missing_ok=True)
 for path in baseline.glob('*.dart'): path.unlink()
 baseline.rmdir()
