from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
def edit(path, old, new):
 p=root/path
 s=p.read_text()
 assert old in s, (path,old[:80])
 p.write_text(s.replace(old,new))
base='apps/sokoun_app/lib/'
edit(base+'features/shared/profile/presentation/widgets/shared/profile_scaffold.dart', 'return AppScaffold(', 'return AppScaffold(\n      contentWidth: SokounContentWidth.wide,')
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
