import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/custom_shimmer.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_home_data.dart';
import 'home_property_item.dart';
import 'tenant_home_header.dart';
import 'tenant_suggested_properties_empty_state.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/cubits/rent_overview_cubit.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_overview_section.dart';

class TenantHomeContent extends StatefulWidget {
  const TenantHomeContent({super.key});
  @override
  State<TenantHomeContent> createState() => _TenantHomeContentState();
}

class _TenantHomeContentState extends State<TenantHomeContent> {
  final TenantHomeData _data = TenantHomeData();
  final PagifyController<HomePropertyModel> _controller = PagifyController();
  late final ValueNotifier<String?> _banner = ValueNotifier(
    _data.readCachedPage()?.banner,
  );
  int _requestGeneration = 0;
  RentOverviewCubit? _rentCubit;
  Future<void>? _rentRequest;

  @override
  void initState() {
    super.initState();
    if (WorkspaceNavigation.isAuthenticated) {
      _rentCubit = RentOverviewCubit();
      _rentRequest = _refreshRent();
    }
  }

  Future<void> _refreshRent() async => _rentCubit?.load();

  Future<(List<HomePropertyModel>, PaginationData)> _getPage(
    BuildContext context,
    int page,
  ) async {
    if (page == 1) {
      _requestGeneration++;
      if (_requestGeneration > 1) unawaited(_refreshRent());
    }
    final int generation = _requestGeneration;
    final (model, pagination) = await _data.getPage(page: page);
    if (mounted && generation == _requestGeneration && page == 1) {
      _banner.value = model.banner;
    }
    return (model.results, pagination);
  }

  @override
  void dispose() {
    _banner.dispose();
    _rentCubit?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.symmetric(horizontal: 20.w),
    child: AppPagify<HomePropertyModel>(
      enablePullRefresh: true,
      pagifyController: _controller,
      asyncCall: _getPage,
      shrinkWrap: false,
      physics: const AlwaysScrollableScrollPhysics(),
      rankingType: Ranking.adaptiveGrid,
      header: ValueListenableBuilder<String?>(
        valueListenable: _banner,
        builder: (context, banner, _) => TenantHomeHeader(
          banner: banner,
          rentOverview: _rentCubit == null
              ? null
              : RentOverviewSection(
                  cubit: _rentCubit!,
                  request: _rentRequest!,
                  onRefresh: _refreshRent,
                ),
        ),
      ),
      cacheKey: TenantHomeData.cacheKey,
      cacheToJson: (item) => item.toJson(),
      cacheFromJson: HomePropertyModel.fromJson,
      emptyListView: const TenantSuggestedPropertiesEmptyState(),
      errorBuilder: (error) => ExceptionView(
        msg: error.msg,
        onRetry: () async => _controller.retry(),
      ),
      loadingBuilder: const CustomShimmer(
        child: HomePropertyItem(property: HomePropertyModel.initial()),
      ),
      itemBuilder: (context, data, index, item) =>
          HomePropertyItem(property: item),
    ),
  );
}
