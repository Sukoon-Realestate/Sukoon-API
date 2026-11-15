from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib')
p=root/'features/main_view/presentation/widgets/home_screen_content.dart'
s=p.read_text()
old='''                              if (owner._allTabs[bodyIndex].tab !=
                                  WorkspaceTab.messages)'''
new='''                              if (!{
                                WorkspaceTab.messages,
                                WorkspaceTab.visits,
                                WorkspaceTab.profile,
                              }.contains(owner._allTabs[bodyIndex].tab))'''
assert old in s
p.write_text(s.replace(old,new,1))
p=root/'features/shared/profile/imports.dart'
s=p.read_text()
imp="import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';\n"
if imp not in s: s=imp+s
p.write_text(s)
p=root/'features/shared/profile/presentation/widgets/shared/profile_scaffold.dart'
s=p.read_text().replace('''      title: LocaleKeys.profile,
''','''      title: LocaleKeys.profile,
      flatAppBar: true,
''',1)
s=s.replace('''        SokounGlassIconButton(''', '''        IconButton(''')
s=s.replace('''      ],
      body: body,''','''        if (WorkspaceNavigation.isAuthenticated)
          NotificationBellButton(
            role: workspace.isOwner ? NotificationRole.owner : NotificationRole.tenant,
          ),
      ],
      body: body,''',1)
p.write_text(s)
p=root/'features/tenant/visits/imports.dart'
s=p.read_text()
for imp in [
"import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';\n",
"import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';\n",
"import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';\n",
"import 'package:sokoun_app/features/shared/profile/imports.dart' show ProfileSettingsScreen;\n",
]:
 if imp not in s: s=imp+s
p.write_text(s)
p=root/'features/tenant/visits/presentation/screens/tenant_visits_screen.dart'
s=p.read_text()
old='''      title: LocaleKeys.tenantVisitsTitle,
      showBackButton: widget.showBackButton,'''
new='''      title: LocaleKeys.tenantVisitsTitle,
      flatAppBar: true,
      showBackButton: widget.showBackButton,
      actions: [
        if (WorkspaceNavigation.isAuthenticated &&
            WorkspaceCubit.instance.state.workspace.isCompany)
          IconButton(
            tooltip: LocaleKeys.profileSettingsTitle,
            icon: const Icon(Icons.manage_accounts_outlined),
            onPressed: () => Go.to(const ProfileSettingsScreen(workspace: AppWorkspace.company)),
          ),
        if (WorkspaceNavigation.isAuthenticated)
          NotificationBellButton(role: NotificationRole.tenant),
      ],'''
assert old in s
p.write_text(s.replace(old,new,1))
