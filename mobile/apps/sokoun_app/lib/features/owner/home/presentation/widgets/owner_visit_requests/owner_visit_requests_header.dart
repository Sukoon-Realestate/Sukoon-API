import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_requests_response.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

import 'owner_visit_request_filters.dart';
import 'owner_visit_request_summary_grid.dart';

class OwnerVisitRequestsHeader extends StatelessWidget {
  const OwnerVisitRequestsHeader({
    super.key,
    required this.requests,
    required this.selectedFilter,
    required this.onFilterSelected,
    this.response,
  });

  final List<OwnerVisitRequestContent> requests;
  final OwnerVisitRequestsResponse? response;
  final OwnerVisitRequestFilter selectedFilter;
  final ValueChanged<OwnerVisitRequestFilter> onFilterSelected;

  int _countForFilter(OwnerVisitRequestFilter filter) {
    final Map<String, int> tabs = response?.tabs ?? const {};
    final int? count = switch (filter) {
      OwnerVisitRequestFilter.all => tabs['all'] ?? response?.count,
      OwnerVisitRequestFilter.newRequests => tabs['new'] ?? tabs['pending'],
      OwnerVisitRequestFilter.accepted => tabs['confirmed'] ?? tabs['accepted'],
      OwnerVisitRequestFilter.rejected => tabs['rejected'],
      OwnerVisitRequestFilter.completed => tabs['completed'],
    };
    return count ??
        requests.where((request) => filter.accepts(request.status)).length;
  }

  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 14.h),
    decoration: BoxDecoration(
      color: context.appColor(AppColors.white, surface: true),
      border: Border(
        bottom: BorderSide(color: context.appColor(AppColors.grayPale)),
      ),
    ),
    child: Column(
      spacing: 12.h,
      children: [
        OwnerVisitRequestSummaryGrid(
          totalCount: _countForFilter(OwnerVisitRequestFilter.all),
          pendingCount: _countForFilter(OwnerVisitRequestFilter.newRequests),
        ),
        OwnerVisitRequestFilters(
          filters: OwnerVisitRequestFilter.values,
          selectedFilter: selectedFilter,
          countForFilter: _countForFilter,
          onFilterSelected: onFilterSelected,
        ),
      ],
    ),
  );
}
