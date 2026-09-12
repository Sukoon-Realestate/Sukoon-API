import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';

import '../widgets/imports.dart';
import 'notification_detail_screen.dart';
import 'notification_settings_screen.dart';
import 'notifications_empty_screen.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key, this.role, this.initialNotifications});

  final NotificationRole? role;
  final List<AppNotificationContent>? initialNotifications;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  late final NotificationRole _role;
  late List<AppNotificationContent> _notifications;

  @override
  void initState() {
    super.initState();
    _role = _resolveRole(widget.role);
    _notifications = List<AppNotificationContent>.of(
      widget.initialNotifications ?? NotificationsContent.forRole(_role),
    );
  }

  NotificationRole _resolveRole(NotificationRole? role) {
    if (role != null) {
      return role;
    }

    return UserTypeHelper.instance.currentUserType.isOwner
        ? NotificationRole.owner
        : NotificationRole.tenant;
  }

  bool get _hasUnread =>
      _notifications.any((notification) => notification.isUnread);

  void _markAllAsRead() {
    if (!_hasUnread) {
      return;
    }

    setState(() {
      _notifications = _notifications
          .map((notification) => notification.copyWith(isUnread: false))
          .toList(growable: false);
    });
  }

  void _openNotification(AppNotificationContent notification) {
    final int index = _notifications.indexWhere(
      (item) => item.id == notification.id,
    );
    if (index != -1 && notification.isUnread) {
      setState(() {
        _notifications[index] = notification.copyWith(isUnread: false);
      });
    }

    Go.to(NotificationDetailScreen(role: _role, notification: notification));
  }

  @override
  Widget build(BuildContext context) {
    if (_notifications.isEmpty) {
      return NotificationsEmptyScreen(role: _role);
    }

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _NotificationsHeader(
                role: _role,
                hasUnread: _hasUnread,
                onMarkAllPressed: _markAllAsRead,
              ),
              Expanded(
                child: ListView.separated(
                  padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 18.h),
                  itemBuilder: (context, index) {
                    final AppNotificationContent notification =
                        _notifications[index];
                    return NotificationCard(
                      key: ValueKey(notification.id),
                      notification: notification,
                      onPressed: () => _openNotification(notification),
                    );
                  },
                  separatorBuilder: (context, index) => 8.szH,
                  itemCount: _notifications.length,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationsHeader extends StatelessWidget {
  const _NotificationsHeader({
    required this.role,
    required this.hasUnread,
    required this.onMarkAllPressed,
  });

  final NotificationRole role;
  final bool hasUnread;
  final VoidCallback onMarkAllPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: AppText(
            LocaleKeys.notificationsFlowTitle,
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        TextButton(
          onPressed: hasUnread ? onMarkAllPressed : null,
          style: TextButton.styleFrom(
            foregroundColor: AppColors.sokoonTeal,
            padding: EdgeInsets.symmetric(horizontal: 6.w),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: AppText(
            role.isOwner
                ? LocaleKeys.notificationsMarkAll
                : LocaleKeys.notificationsMarkAllRead,
            color: hasUnread ? AppColors.sokoonTeal : AppColors.sokoonMuted,
            fontSize: 12.sp,
            fontWeight: FontWeight.w800,
          ),
        ),
        IconButton(
          tooltip: LocaleKeys.notificationSettingsTitle,
          onPressed: () => Go.to(NotificationSettingsScreen(role: role)),
          visualDensity: VisualDensity.compact,
          constraints: BoxConstraints.tightFor(width: 38.r, height: 38.r),
          padding: EdgeInsets.zero,
          icon: Icon(
            Icons.settings_outlined,
            color: AppColors.sokoonNavy,
            size: 20.r,
          ),
        ),
      ],
    ).padding(EdgeInsets.fromLTRB(20.w, 4.h, 14.w, 12.h));
  }
}
