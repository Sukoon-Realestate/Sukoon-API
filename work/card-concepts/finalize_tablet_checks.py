from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
p=root/'apps/sokoun_app/lib/features/shared/profile/imports.dart'
s=p.read_text();p.write_text(s.replace("import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';\n",''))
p=root/'apps/sokoun_app/test/tablet_responsiveness_test.dart'
s=p.read_text()
point="  testWidgets('tablet sheet width and keyboard ownership'"
pos=s.index(point)
s=s[:pos]+'''  for (final workspace in AppWorkspace.values) {
    for (final scale in [1.0, 2.0]) {
      testWidgets('tablet settings $workspace text=$scale', (tester) async {
        tester.view.physicalSize = const Size(1024, 1366);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        await tester.pumpWidget(featureTestHost(
          ProfileSettingsScreen(workspace: workspace), scale: scale));
        await tester.pumpAndSettle();
        final sections = find.byType(ProfileMenuSection);
        expect(sections, findsAtLeastNWidgets(2));
        final first = tester.getRect(sections.at(0));
        final second = tester.getRect(sections.at(1));
        if (scale == 1) {
          expect(first.top, closeTo(second.top, 1));
        } else {
          expect(second.top, greaterThan(first.top));
        }
        final logout = find.byType(ProfileLogoutButton);
        await tester.ensureVisible(logout);
        await tester.pumpAndSettle();
        expect(logout.hitTestable(), findsOneWidget);
        expect(tester.takeException(), isNull);
      });
    }
  }
''' +s[pos:]
p.write_text(s)
