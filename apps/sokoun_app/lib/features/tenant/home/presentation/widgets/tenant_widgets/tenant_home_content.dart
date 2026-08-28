import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/object.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/home_page_cubit.dart';

import 'home_search_box.dart';
import 'home_section_header.dart';
import 'suggested_properties_section.dart';
import 'tenant_header.dart';
import 'tenant_visit_banner.dart';

class TenantHomeContent extends StatefulWidget {
  const TenantHomeContent({
    required this.onNotificationsPressed,
    required this.onSearchPressed,
    required this.onVisitPressed,
    required this.onPropertyPressed,
    super.key,
  });

  final VoidCallback onNotificationsPressed;
  final VoidCallback onSearchPressed;
  final VoidCallback onVisitPressed;
  final ValueChanged<String> onPropertyPressed;

  @override
  State<TenantHomeContent> createState() => _TenantHomeContentState();
}

class _TenantHomeContentState extends State<TenantHomeContent> {
  late final HomePageCubit _homePageCubit;
  late final Future<void> _homePageRequest;

  @override
  void initState() {
    super.initState();
    _homePageCubit = HomePageCubit();
    _homePageRequest = _homePageCubit.getHomePage();
  }

  @override
  void dispose() {
    _homePageCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _homePageCubit,
      child: StatusBuilder<HomePageCubit, HomePageModel>.withShimmer(
        initialDataForShimmer: HomePageModel.initial(),
        requestToTryAgainWhenError: _homePageRequest,
        builder: (data) => _TenantHomeBody(
          showVisitBanner: data.banner.isNotNull,
          requestToTryAgainWhenError: _homePageRequest,
          onNotificationsPressed: widget.onNotificationsPressed,
          onSearchPressed: widget.onSearchPressed,
          onVisitPressed: widget.onVisitPressed,
          onPropertyPressed: widget.onPropertyPressed,
        ),
      ),
    );
  }
}

class _TenantHomeBody extends StatelessWidget {
  const _TenantHomeBody({
    required this.showVisitBanner,
    required this.requestToTryAgainWhenError,
    required this.onNotificationsPressed,
    required this.onSearchPressed,
    required this.onVisitPressed,
    required this.onPropertyPressed,
  });

  final bool showVisitBanner;
  final Future<void> requestToTryAgainWhenError;
  final VoidCallback onNotificationsPressed;
  final VoidCallback onSearchPressed;
  final VoidCallback onVisitPressed;
  final ValueChanged<String> onPropertyPressed;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TenantHeader(onNotificationsPressed: onNotificationsPressed),
          18.szH,
          HomeSearchBox(onPressed: onSearchPressed),
          16.szH,
          TenantVisitBanner(
            onPressed: onVisitPressed,
          ).showIf(condition: () => showVisitBanner),
          18.szH,
          HomeSectionHeader(
            title: LocaleKeys.tenantHomeSuggestedForYou,
            actionTitle: LocaleKeys.tenantHomeViewAll,
            onActionTap: () {},
          ),
          10.szH,
          SuggestedPropertiesSection(
            requestToTryAgainWhenError: requestToTryAgainWhenError,
            onPropertyPressed: onPropertyPressed,
          ),
          24.szH,
        ],
      ),
    );
  }
}
