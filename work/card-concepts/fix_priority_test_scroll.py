from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/account_pages_cleanup_layout_test.dart')
s=p.read_text().replace('await tester.ensureVisible(priority(LocaleKeys.exPriorityAmenities));\n    await tester.tap', 'await tester.ensureVisible(priority(LocaleKeys.exPriorityAmenities));\n    await tester.pumpAndSettle();\n    await tester.tap')
p.write_text(s)
