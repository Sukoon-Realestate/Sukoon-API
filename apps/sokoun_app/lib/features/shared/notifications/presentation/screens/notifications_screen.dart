import 'notification_settings_screen.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:pagify/pagify.dart';

import '../../data/enums/notification_role.dart';
import '../../data/models/app_notification_content.dart';
import '../../data/models/notification_operations_state.dart';
import '../cubits/notifications_cubit.dart';
import '../widgets/notifications_read_action.dart';
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
  late final ValueNotifier<List<AppNotificationContent>?> _fixtureNotifications;
  PagifyController<AppNotificationContent>? _pagifyController;

  @override
  void initState() {
    super.initState();
    _role = _resolveRole(widget.role);
    _cubit = NotificationsCubit();
    final List<AppNotificationContent>? initialNotifications =
        widget.initialNotifications;
    _fixtureNotifications = ValueNotifier<List<AppNotificationContent>?>(
      initialNotifications == null
          ? null
          : List<AppNotificationContent>.of(initialNotifications),
    );
    if (_fixtureNotifications.value == null) {
      _pagifyController = PagifyController<AppNotificationContent>();
    } else {
      _cubit.setUnreadCount(
        _fixtureNotifications.value!.where((item) => item.isUnread).length,
      );
    }
  }

  @override
  void dispose() {
    _fixtureNotifications.dispose();
    _cubit.close();
    super.dispose();
  }

  NotificationRole _resolveRole(NotificationRole? role) {
    if (role != null) return role;
    return injector.isRegistered<WorkspaceCubit>() &&
            WorkspaceCubit.instance.state.isOwner
        ? NotificationRole.owner
        : NotificationRole.tenant;
  }

  Future<void> _markAllAsRead() async {
    final List<AppNotificationContent>? fixtures = _fixtureNotifications.value;
    if (fixtures != null) {
      _fixtureNotifications.value = fixtures
          .map((notification) => notification.copyWith(isRead: true))
          .toList(growable: false);
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
    final List<AppNotificationContent>? fixtures = _fixtureNotifications.value;
    if (fixtures != null) {
      final int index = fixtures.indexWhere(
        (item) => item.id == notification.id,
      );
      if (index >= 0 && notification.isUnread) {
        final List<AppNotificationContent> updated =
            List<AppNotificationContent>.of(fixtures);
        updated[index] = notification.copyWith(isRead: true);
        _fixtureNotifications.value = updated;
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
    return BlocProvider<NotificationsCubit>.value(
      value: _cubit,
      child: AppScaffold(
        title: LocaleKeys.workspaceAllNotifications,
        showBackButton: true,
        actions: [
          BlocSelector<
            NotificationsCubit,
            AsyncState<NotificationOperationsState>,
            bool
          >(
            selector: (state) => state.data.isMarkingAll,
            builder: (context, isMarkingAll) => IconButton(
              tooltip: LocaleKeys.notificationSettingsTitle,
              onPressed: isMarkingAll
                  ? null
                  : () => Go.to(NotificationSettingsScreen(role: _role)),
              icon: const Icon(Icons.settings_outlined),
            ),
          ),
        ],
        backgroundColor: context.appColor(
          AppColors.scaffoldBackground,
          surface: true,
        ),
        body: SafeArea(
          child: ValueListenableBuilder<List<AppNotificationContent>?>(
            valueListenable: _fixtureNotifications,
            builder: (context, fixtureNotifications, _) => NotificationsList(
              role: _role,
              initialNotifications: fixtureNotifications,
              pagifyController: _pagifyController,
              onNotificationPressed: _openNotification,
              onUnreadCountChanged: _cubit.setUnreadCount,
              header:
                  BlocSelector<
                    NotificationsCubit,
                    AsyncState<NotificationOperationsState>,
                    ({bool hasUnread, bool isMarkingAll})
                  >(
                    selector: (state) => (
                      hasUnread: state.data.unreadCount > 0,
                      isMarkingAll: state.data.isMarkingAll,
                    ),
                    builder: (context, state) => NotificationsReadAction(
                      role: _role,
                      hasUnread: state.hasUnread,
                      isMarkingAll: state.isMarkingAll,
                      onMarkAllPressed: _markAllAsRead,
                    ),
                  ),
            ),
          ),
        ),
      ),
    );
  }
}
