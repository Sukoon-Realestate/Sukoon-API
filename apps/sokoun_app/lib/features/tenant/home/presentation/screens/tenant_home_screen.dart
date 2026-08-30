import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/home_page_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import '../widgets/tenant_widgets/imports.dart';
import 'tenant_search_screen.dart';

class TenantHomeScreen extends StatefulWidget {
  const TenantHomeScreen({super.key});

  @override
  State<TenantHomeScreen> createState() => _TenantHomeScreenState();
}

class _TenantHomeScreenState extends State<TenantHomeScreen> {
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
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: BlocProvider<HomePageCubit>.value(
            value: _homePageCubit,
            child: StatusBuilder<HomePageCubit, HomePageModel>.withShimmer(
              initialDataForShimmer: const HomePageModel.initial(),
              requestToTryAgainWhenError: _homePageRequest,
              errorType: ErrorType.defaultView,
              builder: (data) => TenantHomeContent(
                properties: data.results,
                showVisitBanner: data.banner != null,
                onNotificationsPressed: () => Go.to(
                  const NotificationsScreen(role: NotificationRole.tenant),
                ),
                onSearchPressed: () => Go.to(const TenantSearchScreen()),
                onVisitPressed: () => Go.to(const TenantVisitsScreen()),
                onPropertyPressed: (propertyId) =>
                    Go.to(PropertyDetailsScreen(propertyId: propertyId)),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
