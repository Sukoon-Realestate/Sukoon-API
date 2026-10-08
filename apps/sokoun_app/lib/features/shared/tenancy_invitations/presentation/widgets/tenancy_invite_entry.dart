import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../data/models/tenancy_invitation.dart';
import '../screens/tenancy_invite_screen.dart';
import '../screens/tenancy_invitation_detail_screen.dart';

class TenancyInviteEntry extends StatelessWidget {
  const TenancyInviteEntry({
    super.key,
    required this.propertyId,
    required this.propertyTitle,
    required this.tenantId,
    required this.tenantName,
    this.enabled = true,
  });
  final String propertyId, propertyTitle, tenantId, tenantName;
  final bool enabled;

  Future<void> _open(BuildContext context) async {
    final invitation = await Go.to<TenancyInvitation>(
      TenancyInviteScreen(
        propertyId: propertyId,
        propertyTitle: propertyTitle,
        tenantId: tenantId,
        tenantName: tenantName,
      ),
    );
    if (invitation != null && context.mounted) {
      await Go.to<void>(
        TenancyInvitationDetailScreen(
          invitationId: invitation.id,
          workspace: AppWorkspace.owner,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: enabled && propertyId.isNotEmpty && tenantId.isNotEmpty
        ? () => _open(context)
        : null,
    icon: const Icon(Icons.mail_outline),
    label: AppText(LocaleKeys.tenancyInviteToRent),
  );
}
