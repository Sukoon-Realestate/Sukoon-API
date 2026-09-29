import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';

import '../widgets/notifications_empty_state.dart';

class NotificationsEmptyScreen extends StatelessWidget {
  const NotificationsEmptyScreen({super.key, required this.role});

  final NotificationRole role;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      showBackButton: false,
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
                fontWeight: FontWeight.w700,
              ),
            ),
            Expanded(child: NotificationsEmptyState(role: role)),
          ],
        ),
      ),
    );
  }
}
