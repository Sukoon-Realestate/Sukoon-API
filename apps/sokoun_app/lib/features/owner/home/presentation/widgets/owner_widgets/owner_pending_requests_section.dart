import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';

import 'home_section_header.dart';
import 'owner_pending_requests_empty_state.dart';
import 'owner_request_card.dart';

class OwnerPendingRequestsSection extends StatelessWidget {
  const OwnerPendingRequestsSection({super.key, required this.pendingVisits});

  final List<OwnerDashboardPendingVisitModel> pendingVisits;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        HomeSectionHeader(title: LocaleKeys.ownerDashboardPendingTitle),
        10.szH,
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
                visit.propertyDistrict,
                visit.scheduledAt,
              ].where((value) => value.isNotEmpty).join(' · ');
              return OwnerRequestCard(
                key: ValueKey(visit.id),
                requestId: visit.id,
                name: visit.tenantName,
                avatarUrl: visit.tenantAvatar,
                details: details,
              );
            },
          ),
      ],
    );
  }
}
