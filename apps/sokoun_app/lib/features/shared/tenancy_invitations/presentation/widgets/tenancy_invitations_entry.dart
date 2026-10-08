import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../screens/tenancy_invitations_screen.dart';

class TenancyInvitationsEntry extends StatelessWidget {
  const TenancyInvitationsEntry({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => ListTile(
    leading: const Icon(Icons.mail_outline),
    title: AppText(LocaleKeys.tenancyInvitations),
    subtitle: AppText(LocaleKeys.tenancyInvitationsEntryBody),
    trailing: const Icon(Icons.chevron_right),
    onTap: () => Go.to(TenancyInvitationsScreen(workspace: workspace)),
  );
}
