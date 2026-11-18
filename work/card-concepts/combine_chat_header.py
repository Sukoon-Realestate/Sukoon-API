from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib')
p=root/'features/main_view/presentation/widgets/home_screen_content.dart'
s=p.read_text()
old='''                              WorkspaceHeader(
'''
assert s.count(old)==1
s=s.replace(old,'''                              if (owner._allTabs[bodyIndex].tab != WorkspaceTab.messages)
                              WorkspaceHeader(
''',1)
p.write_text(s)
p=root/'features/shared/chat/presentation/screens/chats_screen.dart'
s=p.read_text()
s="""import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart' show ProfileSettingsScreen;
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
"""+s
s=s.replace('''    title: LocaleKeys.chatConversationsTitle,
    showBackButton: false,''','''    title: LocaleKeys.chatConversationsTitle,
    flatAppBar: true,
    showBackButton: false,''')
old='''    actions: [
'''
new='''    actions: [
      if (WorkspaceNavigation.isAuthenticated && _scope == AppWorkspace.company.name)
        IconButton(
          tooltip: LocaleKeys.profileSettingsTitle,
          icon: const Icon(Icons.manage_accounts_outlined),
          onPressed: () => Go.to(const ProfileSettingsScreen(workspace: AppWorkspace.company)),
        ),
'''
assert s.count(old)==1
s=s.replace(old,new)
old='''        icon: const Icon(Icons.storage_outlined),
      ),
    ],'''
new='''        icon: const Icon(Icons.storage_outlined),
      ),
      if (WorkspaceNavigation.isAuthenticated)
        NotificationBellButton(
          role: _scope == AppWorkspace.owner.name
            ? NotificationRole.owner : NotificationRole.tenant,
        ),
    ],'''
assert old in s
p.write_text(s.replace(old,new))
