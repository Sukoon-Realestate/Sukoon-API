from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
def edit(path, old, new):
 p=root/path
 s=p.read_text()
 assert old in s, (path,old[:80])
 p.write_text(s.replace(old,new))
base='apps/sokoun_app/lib/'
edit(base+'shared_widgets/sokoun_layout.dart', '  static const double detailBreakpoint = 960;', '''  static const double detailBreakpoint = 960;

  /// Give enlarged navigation labels room without squeezing the active page.
  static double navigationWidth(BuildContext context) =>
      (104 * (MediaQuery.textScalerOf(context).scale(12) / 12))
          .clamp(104, 160).toDouble();

  static bool usesNavigationRail(BuildContext context, double availableWidth) =>
      availableWidth >= navigationBreakpoint &&
      availableWidth - navigationWidth(context) >= 480;''')
edit(base+'features/main_view/presentation/widgets/home_screen_content.dart', '''                final bool rail =
                    constraints.maxWidth >= SokounLayout.navigationBreakpoint;''', '''                final insets = MediaQuery.paddingOf(context);
                final bool rail = SokounLayout.usesNavigationRail(
                  context, constraints.maxWidth - insets.horizontal,
                );''')
edit(base+'features/main_view/presentation/widgets/home_screen_content.dart', '''                        width: rail ? 104 : 0,
                        child: rail ? owner._buildNavigation(rail: true) : null,''', '''                        width: rail
                            ? SokounLayout.navigationWidth(context) + insets.horizontal
                            : 0,
                        child: rail
                            ? SafeArea(child: owner._buildNavigation(rail: true))
                            : null,''')
p=base+'shared_widgets/app_scaffold.dart'
edit(p, '''  Widget build(BuildContext context) {
    final header = _hasAppBar ? _buildAppBar(context) : null;''', '''  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) => _build(context, constraints.maxWidth),
  );

  Widget _build(BuildContext context, double availableWidth) {
    final double toolbarWidth = availableWidth.clamp(0, contentWidth.maxWidth)
        .toDouble();
    final bar = _hasAppBar ? _buildAppBar(context, toolbarWidth) : null;
    final header = bar == null ? null : PreferredSize(
      preferredSize: bar.preferredSize,
      child: SokounContent(width: contentWidth, child: bar),
    );''')
edit(p, 'if (workspaceHeader != null) workspaceHeader,', 'if (workspaceHeader != null)\n                    SokounContent(width: contentWidth, child: workspaceHeader),')
edit(p, 'if (pageHeader != null) pageHeader!,', 'if (pageHeader != null)\n                    SokounContent(width: contentWidth, child: pageHeader!),')
edit(p, '                pageHeader!,', '                SokounContent(width: contentWidth, child: pageHeader!),')
edit(p, 'PreferredSizeWidget _buildAppBar(BuildContext context) {', 'PreferredSizeWidget _buildAppBar(BuildContext context, double availableWidth) {')
edit(p, 'actions.length > 2 && MediaQuery.sizeOf(context).width < 600;', 'actions.length > 2 && availableWidth < 600;')
edit(p, '''        context,
        leadingWidth: hasLeading''', '''        context,
        availableWidth: availableWidth,
        leadingWidth: hasLeading''')
edit(p, '''              SokounToolbarActions(
                leadingWidth:''', '''              SokounToolbarActions(
                availableWidth: availableWidth,
                leadingWidth:''')
edit(p, 'child: SokounToolbarActions(children: actions),', 'child: SokounToolbarActions(availableWidth: availableWidth, children: actions),')
edit(p, '''    required double leadingWidth,
    required bool separateActions,''', '''    required double availableWidth,
    required double leadingWidth,
    required bool separateActions,''')
edit(p, '''        MediaQuery.sizeOf(context).width -
        MediaQuery.paddingOf(context).horizontal -''', '''        availableWidth -''')
p=base+'shared_widgets/sokoun_toolbar_actions.dart'
edit(p, '    this.leadingWidth = 0,', '    this.leadingWidth = 0,\n    this.availableWidth,')
edit(p, '  final double leadingWidth;', '  final double leadingWidth;\n  final double? availableWidth;')
edit(p, '''        MediaQuery.sizeOf(context).width -
            MediaQuery.paddingOf(context).horizontal -''', '''        (availableWidth ?? (MediaQuery.sizeOf(context).width -
            MediaQuery.paddingOf(context).horizontal)) -''')
p=base+'features/shared/profile/imports.dart'
if 'sokoun_layout.dart' not in (root/p).read_text():
 (root/p).write_text("import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';\n"+(root/p).read_text())
for role in ['tenant','owner']:
 p=base+f'features/{role}/profile/presentation/screens/{role}_profile_screen.dart'
 edit(p, 'AppScaffold(', 'AppScaffold(\n          contentWidth: SokounContentWidth.wide,')
p=base+'features/shared/profile/presentation/widgets/shared/profile_content_view.dart'
edit(p, '''      ProfileVerificationTile(''', '''      SokounAdaptiveGrid(
        minimumWidth: 300,
        maximumColumns: 2,
        gap: 14,
        children: [
      ProfileVerificationTile(''')
edit(p, '''      14.szH,
      activity,
      14.szH,
      ProfileAccountDetailsCard(details: accountDetails),
      for (final section in additionalSections) ...[14.szH, section],''', '''      activity,
      ProfileAccountDetailsCard(details: accountDetails),
      ...additionalSections,
        ],
      ),''')
# Shared tablet modal width is explicit even for callers using a legacy theme.
edit('packages/core/lib/core/widgets/default_bottom_sheet.dart', '    constraints: constraints,', '    constraints: constraints ?? const BoxConstraints(maxWidth: 640),')
edit('packages/core/lib/core/widgets/default_bottom_sheet.dart', '            width: 1.sw,', '            width: double.infinity,')
p=root/'docs/ui-refactor/REFERENCE-ADAPTATION.md'
p.write_text(p.read_text()+'''\n\n## Tablet layout enhancement — 2026-11-15\n\nAll AppScaffold page toolbars, workspace chrome, page headers and footers now\nalign with the selected form/readable/wide content width. Toolbar title/action\nmeasurement uses that local width, including inside the tablet workspace shell.\nThe rail remains on the reading-start side, with safe-area protection and more\nspace for enlarged labels; narrow split views use the same bottom destinations\nwhen a rail would leave less than 480 logical pixels for the page.\n\nProfile stays in the same main destination for every workspace. The account\nheader remains first; verification, activity, account details and existing role\nsections use up to two columns when local width and text scale allow, and retain\ntheir reading order in a single column otherwise. Forms keep the form width.\nShared modal sheets cap at 640 logical pixels unless a caller supplies its own\nconstraints; keyboard and dismissal ownership are unchanged.\n''')
print('Applied tablet layout enhancements')
