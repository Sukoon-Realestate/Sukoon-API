import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import '../../data/models/digital_lease.dart';
import '../screens/digital_lease_details_screen.dart';

class DigitalLeaseCard extends StatelessWidget {
  const DigitalLeaseCard({
    super.key,
    required this.lease,
    required this.workspace,
    required this.onReturned,
  });
  final DigitalLease lease;
  final AppWorkspace workspace;
  final VoidCallback onReturned;
  @override
  Widget build(BuildContext context) => Card(
    child: InkWell(
      onTap: lease.id.isEmpty
          ? null
          : () async {
              await Go.to(
                DigitalLeaseDetailsScreen(
                  leaseId: lease.id,
                  workspace: workspace,
                ),
              );
              if (context.mounted) onReturned();
            },
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(lease.propertyTitle, fontWeight: FontWeight.bold),
            if (lease.rentalSelection != null)
              AppText(RentalOfferLabels.accommodation(lease.rentalSelection!)),
            8.szH,
            PremiumStatusBadge(status: lease.status),
            AppText(lease.rent.display),
            if (lease.startDate != null && lease.endDate != null)
              AppText(
                '${DateFormat.yMMMd().format(lease.startDate!)} – ${DateFormat.yMMMd().format(lease.endDate!)}',
              ),
          ],
        ),
      ),
    ),
  );
}
