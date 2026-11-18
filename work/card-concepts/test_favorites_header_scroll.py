from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/test/favorites_screen_test.dart')
s=p.read_text()
old='''      expect(find.text(LocaleKeys.uiSavedHeadline), findsOneWidget);
      await tester.tap(
'''
new='''      expect(find.text(LocaleKeys.uiSavedHeadline), findsOneWidget);
      // Scroll property content before opening favorite chats. Page chrome
      // must remain visible rather than inheriting a collapsed outer offset.
      await tester.drag(find.byType(CustomScrollView).first, const Offset(0, -300));
      await tester.pumpAndSettle();
      await tester.tap(
'''
assert s.count(old)==1
s=s.replace(old,new)
old='''      expect(find.byType(FavoriteChatsEmptyState), findsOneWidget);
'''
new='''      expect(find.byType(FavoriteChatsEmptyState), findsOneWidget);
      expect(tester.getRect(find.byType(AppBar)).top, greaterThanOrEqualTo(0));
      expect(tester.getRect(find.byType(AppBar)).bottom,
        lessThanOrEqualTo(tester.getRect(find.byType(TabBar)).top + 1));
'''
assert s.count(old)==1
p.write_text(s.replace(old,new))
