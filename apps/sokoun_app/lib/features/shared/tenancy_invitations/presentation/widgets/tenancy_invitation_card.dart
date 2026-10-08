import 'package:flutter/material.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../data/models/tenancy_invitation.dart';
import '../screens/tenancy_invitation_detail_screen.dart';
import 'tenancy_invitation_labels.dart';

class TenancyInvitationCard extends StatelessWidget {
  const TenancyInvitationCard({
    super.key,
    required this.invitation,
    required this.workspace,
    required this.onReturned,
  });
  final TenancyInvitation invitation;
  final AppWorkspace workspace;
  final VoidCallback onReturned;
  @override
  Widget build(BuildContext context) => SokounContent(
    child: Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: ListTile(
        isThreeLine: true,
        title: AppText(invitation.propertyTitle, fontWeight: FontWeight.bold),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 4,
          children: [
            AppText(
              workspace.isOwner ? invitation.tenantName : invitation.ownerName,
            ),
            AppText(TenancyInvitationLabels.status(invitation)),
          ],
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () async {
          await Go.to<void>(
            TenancyInvitationDetailScreen(
              invitationId: invitation.id,
              workspace: workspace,
            ),
          );
          if (context.mounted) onReturned();
        },
      ),
    ),
  );
}
