import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../widgets/tenancy_invitations_list.dart';

class TenancyInvitationsScreen extends StatelessWidget {
  const TenancyInvitationsScreen({
    super.key,
    required this.workspace,
    this.propertyId = '',
  });
  final AppWorkspace workspace;
  final String propertyId;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.tenancyInvitations,
    showBackButton: true,
    body: SafeArea(
      child: TenancyInvitationsList(
        workspace: workspace,
        propertyId: propertyId,
      ),
    ),
  );
}
