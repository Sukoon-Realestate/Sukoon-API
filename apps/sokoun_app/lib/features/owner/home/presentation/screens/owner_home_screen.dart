import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/owner_dashboard_cubit.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_screen.dart';

import '../widgets/owner_widgets/imports.dart';

class OwnerHomeScreen extends StatefulWidget {
  const OwnerHomeScreen({super.key});

  @override
  State<OwnerHomeScreen> createState() => _OwnerHomeScreenState();
}

class _OwnerHomeScreenState extends State<OwnerHomeScreen> {
  late final OwnerDashboardCubit _ownerDashboardCubit;
  late final Future<void> _ownerDashboardRequest;

  @override
  void initState() {
    super.initState();
    _ownerDashboardCubit = OwnerDashboardCubit();
    _ownerDashboardRequest = _ownerDashboardCubit.getDashboard();
  }

  @override
  void dispose() {
    _ownerDashboardCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: BlocProvider.value(
        value: _ownerDashboardCubit,
        child: Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child:
                StatusBuilder<
                  OwnerDashboardCubit,
                  OwnerDashboardModel
                >.withShimmer(
                  initialDataForShimmer: const OwnerDashboardModel.initial(),
                  requestToTryAgainWhenError: _ownerDashboardRequest,
                  errorType: ErrorType.defaultView,
                  builder: _buildDashboard,
                ),
          ),
        ),
      ),
    );
  }

  Widget _buildDashboard(OwnerDashboardModel dashboard) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OwnerHeader(
            name: dashboard.owner.name,
            avatarUrl: dashboard.owner.avatar,
            isVerified: dashboard.owner.isVerified,
            onNotificationsPressed: () =>
                Go.to(const NotificationsScreen(role: NotificationRole.owner)),
          ),
          18.szH,
          OwnerStatsGrid(
            visitsThisWeek: dashboard.visitsThisWeek,
            activeProperties: dashboard.activeProperties,
            overallRating: dashboard.overallRating,
            pendingRequests: dashboard.pendingRequests,
          ),
          18.szH,
          const HomeSectionHeader(title: 'طلبات انتظار الرد'),
          10.szH,
          if (dashboard.pendingVisits.isEmpty)
            AppText(
              'لا توجد طلبات معلقة',
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w600,
              textAlign: TextAlign.center,
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: dashboard.pendingVisits.length,
              separatorBuilder: (context, index) => 12.szH,
              itemBuilder: (context, index) {
                final OwnerDashboardPendingVisitModel visit =
                    dashboard.pendingVisits[index];
                final String details = [
                  visit.propertyTitle,
                  visit.propertyDistrict,
                  visit.scheduledAt,
                ].where((value) => value.isNotEmpty).join(' · ');
                return OwnerRequestCard(
                  name: visit.tenantName,
                  avatarUrl: visit.tenantAvatar,
                  details: details,
                );
              },
            ),
          24.szH,
        ],
      ),
    );
  }
}
