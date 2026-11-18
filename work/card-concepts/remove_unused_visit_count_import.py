from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/visits/imports.dart')
s=p.read_text().replace("import 'presentation/widgets/tenant_visits/visit_collection_count.dart';\n", '')
p.write_text(s)
