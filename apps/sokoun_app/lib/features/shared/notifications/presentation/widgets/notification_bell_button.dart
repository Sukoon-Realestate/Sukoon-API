import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/enums/notification_role.dart';
import '../../data/models/unread_notifications_content.dart';
import '../cubits/unread_notifications_cubit.dart';
import '../screens/notifications_screen.dart';

class NotificationBellButton extends StatefulWidget {
  const NotificationBellButton({super.key, required this.role});

  final NotificationRole role;

  @override
  State<NotificationBellButton> createState() => _NotificationBellButtonState();
}

class _NotificationBellButtonState extends State<NotificationBellButton> {
  late final UnreadNotificationsCubit _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = UnreadNotificationsCubit()..watchRefreshRequests();
    unawaited(_cubit.loadUnreadCount());
  }

  @override
  void dispose() {
    unawaited(_cubit.close());
    super.dispose();
  }

  Future<void> _openNotifications() async {
    await Go.to<void>(NotificationsScreen(role: widget.role));
    if (mounted) unawaited(_cubit.loadUnreadCount());
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<UnreadNotificationsCubit>.value(
      value: _cubit,
      child:
          BlocBuilder<
            UnreadNotificationsCubit,
            AsyncState<UnreadNotificationsContent>
          >(
            builder: (context, state) {
              final int count = state.data.count;
              return Semantics(
                button: true,
                label: LocaleKeys.notificationsFlowTitle,
                value: count > 0 ? '$count' : null,
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    InkWell(
                      onTap: _openNotifications,
                      customBorder: const CircleBorder(),
                      child: Container(
                        width: 36.r,
                        height: 36.r,
                        decoration: BoxDecoration(
                          color: AppColors.white,
                          shape: BoxShape.circle,
                          border: Border.all(color: AppColors.sokoonBorder),
                        ),
                        child: Icon(
                          Icons.notifications_none_rounded,
                          color: AppColors.sokoonNavy,
                          size: 18.r,
                        ),
                      ),
                    ),
                    if (count > 0)
                      PositionedDirectional(
                        top: -5.r,
                        end: -5.r,
                        child: Container(
                          constraints: BoxConstraints(minWidth: 18.r),
                          height: 18.r,
                          alignment: Alignment.center,
                          padding: EdgeInsets.symmetric(horizontal: 4.w),
                          decoration: BoxDecoration(
                            color: AppColors.red,
                            borderRadius: BorderRadius.circular(999.r),
                            border: Border.all(color: AppColors.white),
                          ),
                          child: AppText(
                            count > 99 ? '99+' : '$count',
                            color: AppColors.white,
                            fontSize: 9.sp,
                            fontWeight: FontWeight.w800,
                            maxLines: 1,
                          ),
                        ),
                      ),
                  ],
                ),
              );
            },
          ),
    );
  }
}
