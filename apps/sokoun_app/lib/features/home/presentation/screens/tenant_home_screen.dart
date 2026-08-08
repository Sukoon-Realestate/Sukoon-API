import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/home/presentation/cubits/home_page_cubit.dart';
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/visits/imports.dart';

import '../widgets/tenant_widgets/imports.dart';

class TenantHomeScreen extends StatefulWidget {
  const TenantHomeScreen({super.key, this.onNotificationsPressed});

  final VoidCallback? onNotificationsPressed;

  @override
  State<TenantHomeScreen> createState() => _TenantHomeScreenState();
}

class _TenantHomeScreenState extends State<TenantHomeScreen> {
  late final HomePageCubit _homePageCubit;

  @override
  void initState() {
    super.initState();
    _homePageCubit = HomePageCubit();
    _homePageCubit.getHomePage();
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
      child: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child: BlocBuilder<HomePageCubit, AsyncState<HomePageModel>>(
              builder: (context, state) {
                return StatusBuilder<HomePageModel, HomePageCubit>(
                  data: state,
                  onSuccess: (data, context) => _buildContent(),
                );
              },
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildContent() {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TenantHeader(
            onNotificationsPressed:
                widget.onNotificationsPressed ??
                () => Go.to(
                  const NotificationsScreen(role: NotificationRole.tenant),
                ),
          ),
          18.szH,
          const HomeSearchBox(),
          16.szH,
          TenantVisitBanner(onPressed: () => Go.to(const TenantVisitsScreen())),
          18.szH,
          HomeSectionHeader(
            title: 'مقترح ليك',
            actionTitle: 'عرض الكل',
            onActionTap: () {},
          ),
          10.szH,
          const SuggestedPropertiesSection(),
          24.szH,
        ],
      ),
    );
  }
}
