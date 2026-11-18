from pathlib import Path
p = Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/details/visit_details_content.dart')
s = p.read_text()
old = '            VisitDetailsActions(\n'
assert s.count(old) == 1
s = s.replace(old, '            const SizedBox(height: 24),\n' + old)
p.write_text(s)
