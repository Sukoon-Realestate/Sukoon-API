import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

import 'owner_visit_request_card.dart';
import 'owner_visit_request_filters.dart';
import 'owner_visit_request_summary_grid.dart';
import 'owner_visit_requests_empty_state.dart';

class OwnerVisitRequestsContent extends StatelessWidget {
  const OwnerVisitRequestsContent({
    super.key,
    required this.requests,
    required this.visibleRequests,
    required this.selectedFilter,
    required this.onFilterSelected,
    required this.onRequestPressed,
    required this.onAcceptPressed,
    required this.onRejectPressed,
    required this.progress,
  });

  final List<OwnerVisitRequestContent> requests;
  final List<OwnerVisitRequestContent> visibleRequests;
  final OwnerVisitRequestFilter selectedFilter;
  final ValueChanged<OwnerVisitRequestFilter> onFilterSelected;
  final ValueChanged<OwnerVisitRequestContent> onRequestPressed;
  final ValueChanged<OwnerVisitRequestContent> onAcceptPressed;
  final ValueChanged<OwnerVisitRequestContent> onRejectPressed;
  final ValueListenable<({String? requestId, OwnerVisitUpdateStatus? status})>
  progress;

  int get _pendingCount =>
      requests.where((request) => request.status.canDecide).length;

  int _countForFilter(OwnerVisitRequestFilter filter) =>
      requests.where((request) => filter.accepts(request.status)).length;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 14.h),
          decoration: const BoxDecoration(
            color: AppColors.white,
            border: Border(bottom: BorderSide(color: AppColors.grayPale)),
          ),
          child: Column(
            spacing: 12.h,
            children: [
              OwnerVisitRequestSummaryGrid(
                totalCount: requests.length,
                pendingCount: _pendingCount,
              ),
              OwnerVisitRequestFilters(
                filters: OwnerVisitRequestFilter.values,
                selectedFilter: selectedFilter,
                countForFilter: _countForFilter,
                onFilterSelected: onFilterSelected,
              ),
            ],
          ),
        ),
        Expanded(
          child: visibleRequests.isEmpty
              ? const OwnerVisitRequestsEmptyState()
              : ListView.separated(
                  padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
                  itemCount: visibleRequests.length,
                  itemBuilder: (context, index) {
                    final OwnerVisitRequestContent request =
                        visibleRequests[index];
                    return ValueListenableBuilder<
                      ({String? requestId, OwnerVisitUpdateStatus? status})
                    >(
                      valueListenable: progress,
                      child: _card(request, null),
                      builder: (context, pending, child) =>
                          pending.requestId == request.id
                          ? _card(request, pending.status)
                          : child!,
                    );
                  },
                  separatorBuilder: (context, index) => 12.szH,
                ),
        ),
      ],
    );
  }

  Widget _card(
    OwnerVisitRequestContent request,
    OwnerVisitUpdateStatus? pendingStatus,
  ) {
    final bool isUpdating = pendingStatus != null;
    return OwnerVisitRequestCard(
      key: ValueKey(request.id),
      request: request,
      onPressed: isUpdating ? null : () => onRequestPressed(request),
      onAcceptPressed: isUpdating ? null : () => onAcceptPressed(request),
      onRejectPressed: isUpdating ? null : () => onRejectPressed(request),
      isAccepting: pendingStatus == OwnerVisitUpdateStatus.confirmed,
      isRejecting: pendingStatus == OwnerVisitUpdateStatus.rejected,
    );
  }
}
