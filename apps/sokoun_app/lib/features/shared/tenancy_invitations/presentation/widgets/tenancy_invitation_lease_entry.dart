import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/lease_draft_screen.dart';
import '../../data/models/tenancy_invitation.dart';

class TenancyInvitationLeaseEntry extends StatelessWidget {
  const TenancyInvitationLeaseEntry({
    super.key,
    required this.invitation,
    required this.onReturned,
  });
  final TenancyInvitation invitation;
  final Future<void> Function() onReturned;
  @override
  Widget build(BuildContext context) => FilledButton.icon(
    onPressed: () async {
      await Go.to<DigitalLease>(
        LeaseDraftScreen(
          property: OwnerPropertyContent.initial().copyWith(
            id: invitation.propertyId,
            title: invitation.propertyTitle,
          ),
        ),
      );
      if (context.mounted) await onReturned();
    },
    icon: const Icon(Icons.draw_outlined),
    label: AppText(LocaleKeys.paidCreateLease),
  );
}
