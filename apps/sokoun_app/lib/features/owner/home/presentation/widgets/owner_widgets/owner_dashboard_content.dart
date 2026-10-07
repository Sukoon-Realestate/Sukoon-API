import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';

import 'owner_pending_requests_section.dart';
import 'owner_stats_grid.dart';
import 'owner_operations_section.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';

class OwnerDashboardContent extends StatelessWidget {
  const OwnerDashboardContent({
    super.key,
    required this.dashboard,
    required this.onRequestResolved,
  });

  final OwnerDashboardModel dashboard;
  final Future<void> Function() onRequestResolved;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SokounReveal(
            child: OwnerPendingRequestsSection(
              pendingVisits: dashboard.pendingVisits,
              onRequestResolved: onRequestResolved,
            ),
          ),
          18.szH,
          SokounReveal(
            delay: const Duration(milliseconds: 60),
            child: OwnerStatsGrid(
              visitsThisWeek: dashboard.visitsThisWeek,
              activeProperties: dashboard.activeProperties,
              overallRating: dashboard.overallRating,
              pendingRequests: dashboard.pendingRequests,
            ),
          ),
          24.szH,
          const OwnerOperationsSection(),
          24.szH,
        ],
      ),
    );
  }
}
