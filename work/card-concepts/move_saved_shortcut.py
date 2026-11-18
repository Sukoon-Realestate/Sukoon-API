from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app')
lib=root/'lib'
p=lib/'features/main_view/presentation/widgets/dashboard_scaffold.dart'
s=p.read_text().replace('    this.primaryAction,','    this.primaryAction,\n    this.headerActions = const [],',1).replace('  final Widget? identity, primaryAction;','  final Widget? identity, primaryAction;\n  final List<Widget> headerActions;',1).replace('                    footer: primaryAction,','                    footer: primaryAction,\n                    actions: headerActions,',1)
p.write_text(s)
p=lib/'features/main_view/presentation/widgets/dashboard_header.dart'
s=p.read_text().replace('    this.footer,','    this.footer,\n    this.actions = const [],',1).replace('  final Widget? identity, footer;','  final Widget? identity, footer;\n  final List<Widget> actions;',1).replace('      identity: identity,','      identity: identity,\n      actions: actions,',1)
s=s.replace('    this.onTools,','    this.onTools,\n    this.actions = const [],',1).replace('  final VoidCallback? onTools;','  final VoidCallback? onTools;\n  final List<Widget> actions;',1).replace('                if (WorkspaceNavigation.isAuthenticated)','                ...actions,\n                if (WorkspaceNavigation.isAuthenticated)',1)
p.write_text(s)
p=lib/'features/tenant/home/presentation/widgets/tenant_widgets/home_search_tools.dart'
s=p.read_text().replace('    required this.onSavedPressed,','    required this.onSavedPressed,\n    this.showSaved = true,',1).replace('  final VoidCallback onAssistantPressed, onSavedPressed;','  final VoidCallback onAssistantPressed, onSavedPressed;\n  final bool showSaved;',1).replace("        GuideTarget(\n          id: 'Saved',","        if (showSaved) GuideTarget(\n          id: 'Saved',",1)
p.write_text(s)
p=lib/'features/tenant/home/presentation/widgets/tenant_widgets/tenant_search_tools.dart'
s=p.read_text().replace('        onSavedPressed: _openSaved,','        onSavedPressed: _openSaved,\n        showSaved: false,',1)
p.write_text(s)
p=lib/'features/tenant/home/presentation/screens/tenant_home_screen.dart'
s=p.read_text()
s="""import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/shared_widgets/sokoun_palette.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/screens/decision_tools_screen.dart';
"""+s
s=s.replace('      title: LocaleKeys.uiHomeHeadline,', '''      title: LocaleKeys.uiHomeHeadline,
      headerActions: [
        GuideTarget(
          id: 'Saved',
          child: IconButton(
            tooltip: LocaleKeys.journeySavedSearches,
            constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
            color: SokounPalette.of(context).onHero,
            icon: const Icon(Icons.bookmarks_outlined, size: 22),
            onPressed: () => WorkspaceNavigation.open(
              workspace: AppWorkspace.tenant,
              detail: () => Go.to(const DecisionToolsScreen()),
            ),
          ),
        ),
      ],''',1)
p.write_text(s)
p=root/'test/home_tools_redesign_test.dart'
s=p.read_text()
# Only the full-screen assertions change; component tests retain their default configuration.
anchor="  testWidgets('Home tools preview below the actual hero'"
a=s.index(anchor)
s=s[:a]+s[a:].replace('expect(find.text(LocaleKeys.journeySavedSearches), findsOneWidget);', '''expect(find.text(LocaleKeys.journeySavedSearches), findsNothing);
    expect(find.byTooltip(LocaleKeys.journeySavedSearches), findsOneWidget);
    final saved = tester.getRect(find.byTooltip(LocaleKeys.journeySavedSearches));
    final search = tester.getRect(find.byType(HomeSearchBox));
    expect(saved.bottom, lessThanOrEqualTo(search.top));
    expect(saved.width, greaterThanOrEqualTo(48));''',1)
s=s.replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/home_search_box.dart';",1)
p.write_text(s)
