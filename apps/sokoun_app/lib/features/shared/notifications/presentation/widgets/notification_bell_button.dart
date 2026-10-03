import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/shared_widgets/sokoun_count_badge.dart';

import '../../data/enums/notification_role.dart';
import '../../../unread_counts/data/models/unread_counts.dart';
import '../screens/notifications_screen.dart';
import 'package:sokoun_app/features/shared/unread_counts/presentation/cubits/unread_counts_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';

class NotificationBellButton extends StatefulWidget {
  const NotificationBellButton({super.key, required this.role});

  final NotificationRole role;

  @override
  State<NotificationBellButton> createState() => _NotificationBellButtonState();
}

class _NotificationBellButtonState extends State<NotificationBellButton> {
  late final UnreadCountsCubit _cubit;
  late final bool _ownsCubit;

  @override
  void initState() {
    super.initState();
    final UnreadCountsCubit? sharedCubit = context.read<UnreadCountsCubit?>();
    _ownsCubit = sharedCubit == null;
    _cubit = sharedCubit ?? UnreadCountsCubit();
    if (_ownsCubit) {
      _cubit.load(workspace: AppWorkspace.tenant);
    }
  }

  @override
  void dispose() {
    if (_ownsCubit) _cubit.close();
    super.dispose();
  }

  Future<void> _openNotifications() async {
    if (!WorkspaceNavigation.isAuthenticated) {
      await WorkspaceNavigation.open(
        showLoginSheet: true,
        detail: () => Go.to<void>(const NotificationsScreen()),
      );
      return;
    }
    await Go.to<void>(NotificationsScreen(role: widget.role));
    if (mounted) {
      await _cubit.refresh(workspace: AppWorkspace.tenant);
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocSelector<UnreadCountsCubit, AsyncState<UnreadCounts>, int>(
      bloc: _cubit,
      selector: (state) => state.data.notificationsCount,
      builder: (context, count) {
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
                  child: SokounCountBadge(count: count, size: 18.r),
                ),
            ],
          ),
        );
      },
    );
  }
}
