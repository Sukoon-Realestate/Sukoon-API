from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/support/imports.dart')
s=p.read_text().replace("import 'package:sokoun_app/shared_widgets/sokoun_hub_header.dart';\n", '')
p.write_text(s)
