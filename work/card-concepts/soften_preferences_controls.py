from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
p=root/'apps/sokoun_app/lib/features/shared/experience/presentation/widgets/discovery_settings.dart'
s=p.read_text()
s="import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';\n"+s
s=s.replace('''                    FilterChip(
                      label:''','''                    FilterChip(
                      side: BorderSide(color: SokounPalette.of(context).line),
                      selectedColor: SokounPalette.of(context).chip,
                      backgroundColor: SokounPalette.of(context).surface,
                      labelStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: SokounPalette.of(context).text, fontWeight: FontWeight.w500, height: 1.5),
                      label:''')
p.write_text(s)
p=root/'apps/sokoun_app/lib/shared_widgets/sokoun_settings_section.dart'
s=p.read_text()
s=s.replace('fontSize: 13,\n              height: 1.5,', 'fontSize: 13,\n              fontWeight: FontWeight.w400,\n              height: 1.5,')
s=s.replace('fontSize: 12,\n              height: 1.5,', 'fontSize: 12,\n              fontWeight: FontWeight.w400,\n              height: 1.5,')
p.write_text(s)
p=root/'apps/sokoun_app/test/account_pages_cleanup_layout_test.dart'
s=p.read_text()
a=s.rfind('\n}')
s=s[:a]+'''
  testWidgets('priority chips keep three-choice limit and ordering', (tester) async {
    await tester.pumpWidget(featureTestHost(const ExperienceSettingsScreen(workspace: AppWorkspace.individual), reducedMotion: false));
    await tester.pumpAndSettle();
    Finder priority(String label) => find.widgetWithText(FilterChip, label);
    for (final label in [LocaleKeys.exPriorityPrice, LocaleKeys.exPrioritySpace, LocaleKeys.exPriorityAmenities]) {
      await tester.ensureVisible(priority(label));
      await tester.tap(priority(label));
      await tester.pumpAndSettle();
    }
    expect(tester.widget<FilterChip>(priority(LocaleKeys.exPriorityCommute)).onSelected, isNull);
    final move = find.text('${LocaleKeys.exMovePriorityUp}: ${LocaleKeys.exPrioritySpace}');
    await tester.ensureVisible(move);
    await tester.tap(move);
    await tester.pumpAndSettle();
    final ranked = tester.widget<FilterChip>(priority(LocaleKeys.exPrioritySpace));
    expect((ranked.avatar as Text).data, '1');
    await tester.ensureVisible(priority(LocaleKeys.exPriorityAmenities));
    await tester.tap(priority(LocaleKeys.exPriorityAmenities));
    await tester.pumpAndSettle();
    expect(tester.widget<FilterChip>(priority(LocaleKeys.exPriorityCommute)).onSelected, isNotNull);
    expect(tester.takeException(), isNull);
  });
''' +s[a:]
p.write_text(s)
