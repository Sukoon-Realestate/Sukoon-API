import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../screens/owner_visit_requests_screen.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';

import 'home_section_header.dart';
import 'owner_pending_requests_empty_state.dart';
import 'owner_request_card.dart';

class OwnerPendingRequestsSection extends StatelessWidget {
  const OwnerPendingRequestsSection({
    super.key,
    required this.pendingVisits,
    required this.onRequestResolved,
  });

  final List<OwnerDashboardPendingVisitModel> pendingVisits;
  final Future<void> Function() onRequestResolved;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 10.h,
      children: [
        Row(
          children: [
            Expanded(
              child: HomeSectionHeader(
                title: LocaleKeys.ownerDashboardPendingTitle,
              ),
            ),
            TextButton(
              onPressed: () => Go.to(
                const OwnerVisitRequestsScreen(useRequestEndpoint: false),
              ),
              child: AppText(LocaleKeys.ownerVisitsTitle),
            ),
          ],
        ),
        if (pendingVisits.isEmpty)
          const OwnerPendingRequestsEmptyState()
        else
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: pendingVisits.length,
            separatorBuilder: (context, index) => 12.szH,
            itemBuilder: (context, index) {
              final OwnerDashboardPendingVisitModel visit =
                  pendingVisits[index];
              final String details = [
                visit.propertyTitle,
                if (visit.rentalSelection != null)
                  RentalOfferLabels.accommodation(visit.rentalSelection!),
                visit.propertyDistrict,
                visit.scheduledAt,
              ].where((value) => value.isNotEmpty).join(' · ');
              return OwnerRequestCard(
                key: ValueKey(visit.id),
                requestId: visit.id,
                name: visit.tenantName,
                avatarUrl: visit.tenantAvatar,
                details: details,
                onRequestResolved: onRequestResolved,
              );
            },
          ),
      ],
    );
  }
}
