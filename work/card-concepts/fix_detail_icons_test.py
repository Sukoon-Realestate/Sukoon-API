from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/property_detail_amenity_icons_test.dart')
s=p.read_text().replace('''          ),
        );
        await tester.pumpAndSettle();''','''          ),
          ),
        );
        await tester.pumpAndSettle();''',1)
p.write_text(s)
