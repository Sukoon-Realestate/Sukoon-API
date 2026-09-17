import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';

import 'owner_header.dart';
import 'owner_pending_requests_section.dart';
import 'owner_stats_grid.dart';

class OwnerDashboardContent extends StatelessWidget {
  const OwnerDashboardContent({super.key, required this.dashboard});

  final OwnerDashboardModel dashboard;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OwnerHeader(
            avatarUrl: dashboard.owner.avatar,
            isVerified: dashboard.owner.isVerified,
          ),
          18.szH,
          OwnerStatsGrid(
            visitsThisWeek: dashboard.visitsThisWeek,
            activeProperties: dashboard.activeProperties,
            overallRating: dashboard.overallRating,
            pendingRequests: dashboard.pendingRequests,
          ),
          18.szH,
          OwnerPendingRequestsSection(pendingVisits: dashboard.pendingVisits),
          24.szH,
        ],
      ),
    );
  }
}
