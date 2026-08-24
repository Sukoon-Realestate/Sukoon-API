import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/object.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/home/presentation/cubits/home_page_cubit.dart';
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/visits/imports.dart';

import '../../../../notifications/presentation/screens/notifications_screen.dart';
import 'home_search_box.dart';
import 'home_section_header.dart';
import 'suggested_properties_section.dart';
import 'tenant_header.dart';
import 'tenant_visit_banner.dart';

class TenantHomeContent extends StatefulWidget {
  const TenantHomeContent({super.key});

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
        ),
      ),
    );
  }
}

class _TenantHomeBody extends StatelessWidget {
  const _TenantHomeBody({
    required this.showVisitBanner,
    required this.requestToTryAgainWhenError,
  });

  final bool showVisitBanner;
  final Future<void> requestToTryAgainWhenError;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TenantHeader(onNotificationsPressed: () => Go.to(
            const NotificationsScreen(role: NotificationRole.tenant),
          )),
          18.szH,
          const HomeSearchBox(),
          16.szH,
          TenantVisitBanner(
            onPressed: () => Go.to(const TenantVisitsScreen()),
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
          ),
          24.szH,
        ],
      ),
    );
  }
}
