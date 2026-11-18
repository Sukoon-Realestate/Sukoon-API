from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
def edit(path,old,new):
 p=root/path;s=p.read_text();assert old in s,(path,old[:60]);p.write_text(s.replace(old,new))
b='apps/sokoun_app/lib/'
edit(b+'shared_widgets/app_scaffold.dart','''    final double toolbarWidth = availableWidth
        .clamp(0, contentWidth.maxWidth)
        .toDouble();''','''    final double safeWidth = availableWidth - MediaQuery.paddingOf(context).horizontal;
    final double toolbarWidth = scrollAppBar
        ? safeWidth.clamp(0, contentWidth.maxWidth).toDouble()
        : (availableWidth.clamp(0, contentWidth.maxWidth) -
            MediaQuery.paddingOf(context).horizontal).clamp(0, double.infinity).toDouble();''')
p=b+'features/shared/profile/presentation/widgets/shared/profile_settings_content_view.dart'
edit(p, '''        if (!MvpScope.enabled && !workspace.isCompany)''', '''        SokounAdaptiveGrid(
          minimumWidth: 300,
          maximumColumns: 2,
          gap: 18,
          children: [
        if (!MvpScope.enabled && !workspace.isCompany)''')
edit(p, '        18.szH,\n', '')
edit(p, '''        AppText(
          LocaleKeys.settingsLegal,''', '''        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
        AppText(
          LocaleKeys.settingsLegal,''')
edit(p, '''        const ProfileSurfaceCard(child: PublicPageMenu()),''', '''        const ProfileSurfaceCard(child: PublicPageMenu()),
          ],
        ),''')
edit(p, '''        24.szH,
        const ProfileLogoutButton(),''', '''          ],
        ),
        24.szH,
        const ProfileLogoutButton(),''')
edit(b+'features/shared/profile/presentation/screens/profile_settings_screen.dart','return AppScaffold(', 'return AppScaffold(\n      contentWidth: SokounContentWidth.wide,')
p=root/'docs/ui-refactor/REFERENCE-ADAPTATION.md'
p.write_text(p.read_text()+'''\nProfile Settings uses the same adaptive section grid: preferences, security,\nlegal links and help retain their labels and destinations; logout and account\ndeletion stay below the sections. Larger text restores the single-column flow.\n''')
