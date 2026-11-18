from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
p=root/'lib/features/tenant/home/presentation/widgets/tenant_widgets/home_search_tools.dart'
s=p.read_text(); start=s.index('        ExplainFeatureButton('); end=s.index('      ],',start); s=s[:start]+s[end:]; p.write_text(s)
p=root/'lib/features/tenant/home/presentation/widgets/tenant_widgets/tenant_home_header.dart'
s=p.read_text().replace('                const ExplainFeatureButton(),\n','')
p.write_text(s)
p=root/'test/home_tools_redesign_test.dart'
s=p.read_text().replace('              LocaleKeys.guideExplainScreen,\n','')
s=s.replace('''            final guideBounds = tester.getRect(
              find.widgetWithText(TextButton, LocaleKeys.guideExplainScreen),
            );''', '''            expect(find.text(LocaleKeys.guideExplainScreen), findsNothing);''')
s=s.replace('            expect(guideBounds.top, greaterThanOrEqualTo(savedBounds.bottom));\n','')
s=s.replace("testWidgets('new guide shortcut replays Search then targets only Saved'", "testWidgets('explicit guide launcher replays Search then targets only Saved'")
start=s.index("  testWidgets('explicit guide launcher")
s=s[:start]+s[start:].replace("                const GuideTarget(id: 'Search', child: Text('Search input')),", "                const GuideTarget(id: 'Search', child: Text('Search input')),\n                const ExplainFeatureButton(),",1)
s=s.replace('expect(find.text(LocaleKeys.guideExplainScreen), findsOneWidget);','expect(find.text(LocaleKeys.guideExplainScreen), findsNothing);')
p.write_text(s)
