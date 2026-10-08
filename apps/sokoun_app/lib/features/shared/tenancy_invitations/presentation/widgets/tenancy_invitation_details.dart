import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_detail_field.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import '../../data/models/tenancy_invitation.dart';
import 'tenancy_invitation_labels.dart';
import 'tenancy_invitation_response_actions.dart';
import 'tenancy_invitation_lease_entry.dart';

class TenancyInvitationDetails extends StatelessWidget {
  const TenancyInvitationDetails({
    super.key,
    required this.invitation,
    required this.workspace,
    required this.isFresh,
    required this.onRefresh,
  });
  final TenancyInvitation invitation;
  final AppWorkspace workspace;
  final bool isFresh;
  final Future<void> Function() onRefresh;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 16,
    children: [
      AppText(
        invitation.propertyTitle,
        fontWeight: FontWeight.bold,
        fontSize: 20,
      ),
      AppText(
        TenancyInvitationLabels.status(invitation),
        fontWeight: FontWeight.bold,
      ),
      Card(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12,
            children: [
              FeatureDetailField(
                label: LocaleKeys.featureLeaseOwner,
                value: invitation.ownerName,
              ),
              FeatureDetailField(
                label: LocaleKeys.ownerVisitTenantLabel,
                value: invitation.tenantName,
              ),
              if (invitation.expiresAt != null)
                FeatureDetailField(
                  label: LocaleKeys.tenancyInvitationExpires,
                  value: DateFormat.yMMMd(
                    Languages.currentLanguage.languageCode,
                  ).add_jm().format(invitation.expiresAt!.toLocal()),
                ),
            ],
          ),
        ),
      ),
      if (invitation.rentalSelection != null)
        RentalSelectionPanel(
          selection: invitation.rentalSelection!,
          historical: true,
        ),
      AppText(LocaleKeys.tenancyInviteExplanation),
      if (invitation.isEligible) AppText(LocaleKeys.tenancyInvitationEligible),
      if (!isFresh) AppText(LocaleKeys.tenancyFreshRequired),
      if (workspace.isTenant)
        TenancyInvitationResponseActions(
          invitation: invitation,
          isFresh: isFresh,
          onRefresh: onRefresh,
        ),
      if (workspace.isOwner && isFresh && invitation.isEligible)
        TenancyInvitationLeaseEntry(
          invitation: invitation,
          onReturned: onRefresh,
        ),
      OutlinedButton.icon(
        onPressed: onRefresh,
        icon: const Icon(Icons.refresh),
        label: AppText(LocaleKeys.tenancyRefreshInvitation),
      ),
    ],
  );
}
