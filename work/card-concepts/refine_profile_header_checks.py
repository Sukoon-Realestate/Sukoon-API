from pathlib import Path
root=Path('/Users/demo23home/code/sukoon/sokoun')
p=root/'apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_scaffold.dart'
s=p.read_text().replace('''        IconButton(
          tooltip: LocaleKeys.profileSettingsTitle,''','''        const SizedBox(width: 8),
        IconButton(
          tooltip: LocaleKeys.profileSettingsTitle,''',1)
s=s.replace('''        if (WorkspaceNavigation.isAuthenticated)
          NotificationBellButton(''','''        if (WorkspaceNavigation.isAuthenticated) ...[
          const SizedBox(width: 8),
          NotificationBellButton(''',1)
s=s.replace('''          ),
      ],
      body: body,''','''          ),
        ],
      ],
      body: body,''',1)
p.write_text(s)
p=root/'apps/sokoun_app/test/profile_flow_test.dart'
s=p.read_text().replace("    if (params.api.startsWith('profiles/') ||\n        params.api.startsWith('auth/') ||\n        params.api == ApiConstants.ownerProfile) {", "    if (!params.api.contains('unread-counts') &&\n        (params.api.startsWith('profiles/') ||\n        params.api.startsWith('auth/') ||\n        params.api == ApiConstants.ownerProfile)) {")
p.write_text(s)
