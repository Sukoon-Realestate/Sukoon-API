import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/pagify.dart';

import '../../data/enums/notification_role.dart';
import '../../data/models/app_notification_content.dart';
import '../../data/notifications_data.dart';
import 'notification_card.dart';
import 'notifications_empty_state.dart';

class NotificationsList extends StatelessWidget {
  const NotificationsList({
    super.key,
    required this.header,
    required this.role,
    required this.initialNotifications,
    required this.pagifyController,
    required this.onNotificationPressed,
    required this.onUnreadCountChanged,
  });

  final NotificationRole role;
  final Widget header;
  final List<AppNotificationContent>? initialNotifications;
  final PagifyController<AppNotificationContent>? pagifyController;
  final ValueChanged<AppNotificationContent> onNotificationPressed;
  final ValueChanged<int> onUnreadCountChanged;

  @override
  Widget build(BuildContext context) {
    final List<AppNotificationContent>? fixtures = initialNotifications;
    if (fixtures != null) {
      return ListView(
        padding: EdgeInsets.only(bottom: 18.h),
        children: [
          header,
          if (fixtures.isEmpty)
            NotificationsEmptyState(role: role)
          else
            for (final notification in fixtures)
              _buildCard(
                notification,
              ).padding(EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 4.h)),
        ],
      );
    }

    return AppPagify<AppNotificationContent>(
      enablePullRefresh: true,
      pagifyController: pagifyController!,
      asyncCall: (_, page) => NotificationsData.getNotificationsPage(
        page: page,
        onUnreadCount: onUnreadCountChanged,
      ),
      shrinkWrap: false,
      header: header,
      contentPadding: EdgeInsets.symmetric(horizontal: 20.w),
      cacheKey: NotificationsData.cacheKey,
      cacheToJson: (notification) => notification.toJson(),
      cacheFromJson: AppNotificationContent.fromJson,
      emptyListView: NotificationsEmptyState(role: role),
      itemBuilder: (context, data, index, notification) => _buildCard(
        notification,
      ).paddingOnly(top: index == 0 ? 4.h : 0, bottom: 8.h),
    ).paddingBottom(18.h);
  }

  Widget _buildCard(AppNotificationContent notification) {
    return NotificationCard(
      key: ValueKey(notification.id),
      notification: notification,
      onPressed: () => onNotificationPressed(notification),
    );
  }
}
