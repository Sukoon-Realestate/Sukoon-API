from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/tablet_responsiveness_test.dart')
s=p.read_text().replace('await tester.ensureVisible(logout);', '''await tester.scrollUntilVisible(logout, 400, scrollable: find.descendant(
            of: find.byType(ListView).first, matching: find.byType(Scrollable)).first);''')
p.write_text(s)
