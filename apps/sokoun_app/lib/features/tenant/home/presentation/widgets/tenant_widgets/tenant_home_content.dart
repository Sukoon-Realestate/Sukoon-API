import 'package:sokoun_app/features/tenant/home/data/public_property_cache.dart';
import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/custom_shimmer.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_home_data.dart';
import 'home_property_item.dart';
import 'tenant_home_header.dart';
import 'tenant_suggested_properties_empty_state.dart';
import '../rental_home/rental_home_sections.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
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
  late final ValueNotifier<HomeVisitBannerModel?> _banner = ValueNotifier(
    _data.readCachedPage()?.banner,
  );
  int _requestGeneration = 0;
  final ValueNotifier<bool> _savedData = ValueNotifier(false);
  final ValueNotifier<int> _sectionRefresh = ValueNotifier(0);
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
      _savedData.value = false;
      _requestGeneration++;
      if (_requestGeneration > 1) {
        unawaited(_refreshRent());
        _sectionRefresh.value++;
      }
    }
    final int generation = _requestGeneration;
    final (model, pagination) = await _data.getPage(page: page);
    if (mounted && generation == _requestGeneration) {
      _savedData.value = _data.fromCache;
    }
    if (mounted && generation == _requestGeneration && page == 1) {
      _banner.value = model.banner;
    }
    return (model.results, pagination);
  }

  @override
  void dispose() {
    _banner.dispose();
    _savedData.dispose();
    _sectionRefresh.dispose();
    _controller.dispose();
    _rentCubit?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.symmetric(horizontal: 20.w),
    child: AppPagify<HomePropertyModel>(
      enablePullRefresh: true,
      pagifyController: _controller,
      disposeController: false,
      asyncCall: _getPage,
      shrinkWrap: false,
      physics: const AlwaysScrollableScrollPhysics(),
      rankingType: Ranking.adaptiveGrid,
      header: ValueListenableBuilder<HomeVisitBannerModel?>(
        valueListenable: _banner,
        builder: (context, banner, _) => Column(
          children: [
            ValueListenableBuilder<bool>(
              valueListenable: _savedData,
              builder: (context, saved, _) => saved
                  ? Padding(
                      padding: const EdgeInsets.all(8),
                      child: Semantics(
                        liveRegion: true,
                        child: AppText(LocaleKeys.professionalSavedData),
                      ),
                    )
                  : const SizedBox.shrink(),
            ),
            TenantHomeHeader(
              banner: banner,
              rentalSections: RentalOfferCapabilities.configured.canSearch
                  ? ValueListenableBuilder<int>(
                      valueListenable: _sectionRefresh,
                      builder: (context, generation, _) =>
                          RentalHomeSections(refreshGeneration: generation),
                    )
                  : null,
              rentOverview: _rentCubit == null
                  ? null
                  : RentOverviewSection(
                      cubit: _rentCubit!,
                      request: _rentRequest!,
                      onRefresh: _refreshRent,
                    ),
            ),
          ],
        ),
      ),
      cacheKey: TenantHomeData.cacheKey,
      cachePolicy: ReadCachePolicy.publicListing,
      canPersistItems: () => !_data.fromCache,
      cacheToJson: (item) => PublicPropertyCache.sanitize(item.toJson()),
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
