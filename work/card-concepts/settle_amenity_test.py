from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/property_amenity_row_test.dart')
s=p.read_text().replace('      expect(find.byIcon(Icons.wifi_outlined)', '      await tester.pumpAndSettle();\n      expect(find.byIcon(Icons.wifi_outlined)',1)
p.write_text(s)
