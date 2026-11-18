from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/property_amenity_row_test.dart')
s=p.read_text().replace("import 'package:easy_localization/easy_localization.dart';", "import 'package:easy_localization/easy_localization.dart' hide TextDirection;")
p.write_text(s)
