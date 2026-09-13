import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:pagify/pagify.dart';

import '../../data/enums/notification_role.dart';
import '../../data/models/app_notification_content.dart';
import '../../data/models/notification_operations_state.dart';
import '../cubits/notifications_cubit.dart';
import '../widgets/notifications_header.dart';
import '../widgets/notifications_list.dart';
import 'notification_detail_screen.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key, this.role, this.initialNotifications});

  final NotificationRole? role;

  /// A test/preview seam. Production callers leave this null to use the API.
  final List<AppNotificationContent>? initialNotifications;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  late final NotificationRole _role;
  late final NotificationsCubit _cubit;
  late final List<AppNotificationContent>? _fixtureNotifications;
  PagifyController<AppNotificationContent>? _pagifyController;

  @override
  void initState() {
    super.initState();
    _role = _resolveRole(widget.role);
    _cubit = NotificationsCubit();
    final List<AppNotificationContent>? initialNotifications =
        widget.initialNotifications;
    _fixtureNotifications = initialNotifications == null
        ? null
        : List<AppNotificationContent>.of(initialNotifications);
    if (_fixtureNotifications == null) {
      _pagifyController = PagifyController<AppNotificationContent>();
    } else {
      _cubit.setUnreadCount(
        _fixtureNotifications.where((item) => item.isUnread).length,
      );
    }
  }

  @override
  void dispose() {
    unawaited(_cubit.close());
    super.dispose();
  }

  NotificationRole _resolveRole(NotificationRole? role) {
    if (role != null) return role;
    return UserTypeHelper.instance.currentUserType.isOwner
        ? NotificationRole.owner
        : NotificationRole.tenant;
  }

  Future<void> _markAllAsRead() async {
    final List<AppNotificationContent>? fixtures = _fixtureNotifications;
    if (fixtures != null) {
      setState(() {
        for (int index = 0; index < fixtures.length; index++) {
          fixtures[index] = fixtures[index].copyWith(isRead: true);
        }
      });
      _cubit.setUnreadCount(0);
      return;
    }

    final bool succeeded = await _cubit.markAllAsRead();
    if (!succeeded || !mounted) return;
    final PagifyController<AppNotificationContent> controller =
        _pagifyController!;
    final List<AppNotificationContent> notifications = controller.items;
    for (int index = 0; index < notifications.length; index++) {
      controller.replaceWith(
        index,
        notifications[index].copyWith(isRead: true),
      );
    }
    await controller.refresh();
  }

  Future<void> _openNotification(AppNotificationContent notification) async {
    final List<AppNotificationContent>? fixtures = _fixtureNotifications;
    if (fixtures != null) {
      final int index = fixtures.indexWhere(
        (item) => item.id == notification.id,
      );
      if (index >= 0 && notification.isUnread) {
        setState(() {
          fixtures[index] = notification.copyWith(isRead: true);
        });
        _cubit.setUnreadCount(_cubit.data.unreadCount - 1);
      }
      await Go.to<void>(
        NotificationDetailScreen(
          role: _role,
          notification: notification.copyWith(isRead: true),
          fetchFromApi: false,
        ),
      );
      return;
    }

    if (notification.isUnread) {
      _replaceNotification(notification.copyWith(isRead: true));
      unawaited(_cubit.markAsRead(notification.id));
    }
    await Go.to<void>(
      NotificationDetailScreen(role: _role, notification: notification),
    );
    if (mounted) await _pagifyController?.refresh();
  }

  void _replaceNotification(AppNotificationContent notification) {
    final PagifyController<AppNotificationContent>? controller =
        _pagifyController;
    if (controller == null) return;
    final int index = controller.items.indexWhere(
      (item) => item.id == notification.id,
    );
    if (index >= 0) controller.replaceWith(index, notification);
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: BlocProvider<NotificationsCubit>.value(
        value: _cubit,
        child: Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child:
                BlocBuilder<
                  NotificationsCubit,
                  AsyncState<NotificationOperationsState>
                >(
                  builder: (context, state) {
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        NotificationsHeader(
                          role: _role,
                          hasUnread: state.data.unreadCount > 0,
                          isMarkingAll: state.data.isMarkingAll,
                          onMarkAllPressed: _markAllAsRead,
                        ),
                        Expanded(
                          child: NotificationsList(
                            role: _role,
                            initialNotifications: _fixtureNotifications,
                            pagifyController: _pagifyController,
                            onNotificationPressed: _openNotification,
                            onUnreadCountChanged: _cubit.setUnreadCount,
                          ),
                        ),
                      ],
                    );
                  },
                ),
          ),
        ),
      ),
    );
  }
}
