import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
    required this.role,
    required this.initialNotifications,
    required this.pagifyController,
    required this.onNotificationPressed,
    required this.onUnreadCountChanged,
  });

  final NotificationRole role;
  final List<AppNotificationContent>? initialNotifications;
  final PagifyController<AppNotificationContent>? pagifyController;
  final ValueChanged<AppNotificationContent> onNotificationPressed;
  final ValueChanged<int> onUnreadCountChanged;

  @override
  Widget build(BuildContext context) {
    final List<AppNotificationContent>? fixtures = initialNotifications;
    if (fixtures != null) {
      if (fixtures.isEmpty) return NotificationsEmptyState(role: role);
      return ListView.separated(
        padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 18.h),
        itemBuilder: (context, index) => _buildCard(fixtures[index]),
        separatorBuilder: (context, index) => 8.szH,
        itemCount: fixtures.length,
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
      cacheKey: NotificationsData.cacheKey,
      cacheToJson: (notification) => notification.toJson(),
      cacheFromJson: AppNotificationContent.fromJson,
      emptyListView: NotificationsEmptyState(role: role),
      itemBuilder: (context, data, index, notification) =>
          _buildCard(notification).paddingBottom(8.h),
    ).padding(EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 18.h));
  }

  Widget _buildCard(AppNotificationContent notification) {
    return NotificationCard(
      key: ValueKey(notification.id),
      notification: notification,
      onPressed: () => onNotificationPressed(notification),
    );
  }
}
