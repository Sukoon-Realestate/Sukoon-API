import 'dart:async';
import 'package:pagify/helpers/status_stream.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/custom_shimmer.dart';
import 'package:melos_core/core/widgets/retry_view.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_home_data.dart';
import 'home_search_box.dart';
import 'home_section_header.dart';
import 'home_property_item.dart';
import 'tenant_header.dart';
import 'tenant_suggested_properties_empty_state.dart';
import 'tenant_visit_banner.dart';

class TenantHomeContent extends StatefulWidget {
  const TenantHomeContent({super.key});
  @override
  State<TenantHomeContent> createState() => _TenantHomeContentState();
}

class _TenantHomeContentState extends State<TenantHomeContent> {
  final TenantHomeData _data = TenantHomeData();
  final PagifyController<HomePropertyModel> _controller = PagifyController();
  late final ValueNotifier<bool> _showBanner = ValueNotifier(
    _data.readCachedPage()?.banner != null,
  );
  Completer<void>? _refreshCompleter;
  int _requestGeneration = 0;

  Future<(List<HomePropertyModel>, PaginationData)> _getPage(
    BuildContext context,
    int page,
  ) async {
    if (page == 1) _requestGeneration++;
    final int generation = _requestGeneration;
    final (model, pagination) = await _data.getPage(page: page);
    if (mounted && generation == _requestGeneration && page == 1) {
      _showBanner.value = model.banner != null;
    }
    return (model.results, pagination);
  }

  Future<void> _refresh() {
    if (_controller.isLoading) return Future.value();
    _refreshCompleter ??= Completer<void>();
    // Pagify's refresh starts the request but returns before it finishes.
    unawaited(_controller.refresh());
    return _refreshCompleter!.future;
  }

  void _completeRefresh() {
    _refreshCompleter?.complete();
    _refreshCompleter = null;
  }

  @override
  void dispose() {
    _completeRefresh();
    _showBanner.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: EdgeInsets.fromLTRB(20.w, 12.h, 20.w, 8.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const TenantHeader(),
            SizedBox(height: 16.h),
            const HomeSearchBox(),
            ValueListenableBuilder<bool>(
              valueListenable: _showBanner,
              builder: (context, visible, _) => visible
                  ? Padding(
                      padding: EdgeInsets.only(top: 16.h),
                      child: const TenantVisitBanner(),
                    )
                  : const SizedBox.shrink(),
            ),
            SizedBox(height: 12.h),
            const HomeSectionHeader(),
          ],
        ),
      ),
      Expanded(
        child: RefreshIndicator(
          onRefresh: _refresh,
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 20.w),
            child: AppPagify<HomePropertyModel>(
              pagifyController: _controller,
              asyncCall: _getPage,
              shrinkWrap: false,
              physics: const AlwaysScrollableScrollPhysics(),
              rankingType: Ranking.adaptiveGrid,
              cacheKey: TenantHomeData.cacheKey,
              cacheToJson: (item) => item.toJson(),
              cacheFromJson: HomePropertyModel.fromJson,
              onUpdateStatus: (status) {
                if (status.isSuccess ||
                    status.isError ||
                    status.isNetworkError) {
                  _completeRefresh();
                }
              },
              onConnectivityChanged: (_) {},
              onError: (_, _, _) {},
              emptyListView: const TenantSuggestedPropertiesEmptyState(),
              errorBuilder: (_) => SingleChildScrollView(
                child: AppRetryView(onRetry: () async => _controller.retry()),
              ),
              loadingBuilder: const CustomShimmer(
                child: HomePropertyItem(property: HomePropertyModel.initial()),
              ),
              itemBuilder: (context, data, index, item) =>
                  HomePropertyItem(property: item),
            ),
          ),
        ),
      ),
    ],
  );
}
