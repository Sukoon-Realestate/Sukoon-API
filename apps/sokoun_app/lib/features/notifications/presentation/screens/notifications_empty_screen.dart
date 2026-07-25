import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/presentation/screens/owner_listings_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_search_screen.dart';
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';

import '../widgets/notifications_empty_state.dart';

class NotificationsEmptyScreen extends StatelessWidget {
  const NotificationsEmptyScreen({super.key, required this.role});

  final NotificationRole role;

  void _exploreProperties() {
    if (role.isOwner) {
      Go.off(const OwnerListingsScreen());
      return;
    }

    Go.off(const TenantSearchScreen());
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
                decoration: const BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: AppColors.sokoonBorder),
                  ),
                ),
                child: AppText(
                  LocaleKeys.notificationsFlowTitle,
                  color: AppColors.sokoonNavy,
                  fontSize: 18.sp,
                  fontWeight: FontWeight.w900,
                ),
              ),
              Expanded(
                child: NotificationsEmptyState(
                  onExplorePressed: _exploreProperties,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
