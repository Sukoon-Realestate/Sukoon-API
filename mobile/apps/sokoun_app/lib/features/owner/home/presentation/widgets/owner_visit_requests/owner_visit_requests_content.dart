import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/custom_loading.dart';
import 'package:melos_core/core/widgets/custom_shimmer.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/owner/visits/data/models/owner_visit_requests_response.dart';
import 'package:sokoun_app/features/owner/visits/data/owner_visit_requests_data.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

import 'owner_visit_request_card.dart';
import 'owner_visit_requests_header.dart';
import 'owner_visit_requests_empty_state.dart';

class OwnerVisitRequestsContent extends StatefulWidget {
  const OwnerVisitRequestsContent({
    super.key,
    required this.initialRequests,
    required this.pagifyController,
    required this.useRequestEndpoint,
    required this.selectedFilter,
    required this.onFilterSelected,
    required this.onRequestPressed,
    required this.onAcceptPressed,
    required this.onRejectPressed,
    required this.progress,
  });

  final List<OwnerVisitRequestContent>? initialRequests;
  final PagifyController<OwnerVisitRequestContent> pagifyController;
  final bool useRequestEndpoint;
  final OwnerVisitRequestFilter selectedFilter;
  final ValueChanged<OwnerVisitRequestFilter> onFilterSelected;
  final ValueChanged<OwnerVisitRequestContent> onRequestPressed;
  final ValueChanged<OwnerVisitRequestContent> onAcceptPressed;
  final ValueChanged<OwnerVisitRequestContent> onRejectPressed;
  final ValueListenable<({String? requestId, OwnerVisitUpdateStatus? status})>
  progress;

  @override
  State<OwnerVisitRequestsContent> createState() =>
      _OwnerVisitRequestsContentState();
}

class _OwnerVisitRequestsContentState extends State<OwnerVisitRequestsContent> {
  late final OwnerVisitRequestsData _data;
  late final ValueNotifier<OwnerVisitRequestsResponse> _summary;
  int _requestGeneration = 0;

  @override
  void initState() {
    super.initState();
    _data = OwnerVisitRequestsData(requests: widget.useRequestEndpoint);
    _summary = ValueNotifier(
      _data.readCachedPage() ?? const OwnerVisitRequestsResponse.initial(),
    );
  }

  @override
  void dispose() {
    _summary.dispose();
    super.dispose();
  }

  Future<(List<OwnerVisitRequestContent>, PaginationData)> _getPage(
    BuildContext context,
    int page,
  ) async {
    if (page == 1) _requestGeneration++;
    final int generation = _requestGeneration;
    final OwnerVisitRequestFilter filter = widget.selectedFilter;
    final (response, pagination) = await _data.getPage(
      page: page,
      filter: filter,
    );
    if (mounted &&
        generation == _requestGeneration &&
        filter.isSame(widget.selectedFilter)) {
      _summary.value = response.tabs.isEmpty
          ? response.copyWith(tabs: _summary.value.tabs)
          : response;
    }
    return (response.results, pagination);
  }

  @override
  Widget build(BuildContext context) {
    final List<OwnerVisitRequestContent>? fixtures = widget.initialRequests;
    if (fixtures != null) {
      final visible = fixtures.where(
        (request) => widget.selectedFilter.accepts(request.status),
      );
      return ListView(
        padding: EdgeInsets.zero,
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          OwnerVisitRequestsHeader(
            requests: fixtures,
            selectedFilter: widget.selectedFilter,
            onFilterSelected: widget.onFilterSelected,
          ),
          if (visible.isEmpty)
            const OwnerVisitRequestsEmptyState()
          else
            for (final request in visible)
              _requestCard(
                request,
              ).padding(EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 0)),
        ],
      );
    }
    return AppPagify<OwnerVisitRequestContent>(
      enablePullRefresh: true,
      pagifyController: widget.pagifyController,
      disposeController: false,
      asyncCall: _getPage,
      shrinkWrap: false,
      header: ValueListenableBuilder<OwnerVisitRequestsResponse>(
        valueListenable: _summary,
        builder: (context, response, _) => OwnerVisitRequestsHeader(
          requests: response.results,
          response: response,
          selectedFilter: widget.selectedFilter,
          onFilterSelected: widget.onFilterSelected,
        ),
      ),
      contentPadding: EdgeInsets.symmetric(horizontal: 16.w),
      cacheKey: _data.cacheKeyFor(widget.selectedFilter),
      cacheToJson: (request) => request.toJson(),
      cacheFromJson: OwnerVisitRequestContent.fromJson,
      onSuccess: (_, requests) {
        if (mounted) {
          _summary.value = _summary.value.copyWith(results: requests);
        }
      },
      emptyListView: const OwnerVisitRequestsEmptyState(),
      loadingBuilder: Builder(
        builder: (_) => widget.pagifyController.items.isEmpty
            ? IgnorePointer(
                child: CustomShimmer(
                  child: _card(OwnerVisitRequestContent.initial(), null),
                ),
              )
            : CustomLoading.showLoadingView().paddingSymmetric(vertical: 12.h),
      ),
      itemBuilder: (context, data, index, request) => _requestCard(
        request,
      ).paddingOnly(top: 12.h, bottom: index == data.length - 1 ? 20.h : 0),
    );
  }

  Widget _requestCard(OwnerVisitRequestContent request) =>
      ValueListenableBuilder<
        ({String? requestId, OwnerVisitUpdateStatus? status})
      >(
        valueListenable: widget.progress,
        child: _card(request, null),
        builder: (context, pending, child) => pending.requestId == request.id
            ? _card(request, pending.status)
            : child!,
      );

  Widget _card(
    OwnerVisitRequestContent request,
    OwnerVisitUpdateStatus? pendingStatus,
  ) {
    final bool isUpdating = pendingStatus != null;
    return OwnerVisitRequestCard(
      key: ValueKey(request.id),
      request: request,
      onPressed: isUpdating ? null : () => widget.onRequestPressed(request),
      onAcceptPressed: isUpdating
          ? null
          : () => widget.onAcceptPressed(request),
      onRejectPressed: isUpdating
          ? null
          : () => widget.onRejectPressed(request),
      isAccepting: pendingStatus == OwnerVisitUpdateStatus.confirmed,
      isRejecting: pendingStatus == OwnerVisitUpdateStatus.rejected,
    );
  }
}
