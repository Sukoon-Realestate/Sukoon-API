from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
p=root/'apps/sokoun_app/lib/features/shared/support/imports.dart'
s=p.read_text().replace("import '../../../shared_widgets/sokoun_selection_chip.dart';\n",'')
p.write_text(s)
p=root/'apps/sokoun_app/test/profile_settings_support_test.dart'
s=p.read_text().replace('await tester.tap(find.byIcon(Icons.verified_user_outlined));', 'await tester.tap(find.byType(ProfileVerificationTile));')
p.write_text(s)
