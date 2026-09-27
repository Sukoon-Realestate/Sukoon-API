import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';

class HomeCircleButton extends StatelessWidget {
  const HomeCircleButton({
    super.key,
    required this.icon,
    required this.iconColor,
    this.backgroundColor = AppColors.white,
    this.showBadge = false,
  });

  final IconData icon;
  final Color iconColor;
  final Color backgroundColor;
  final bool showBadge;

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Semantics(
          button: true,
          child: GestureDetector(
            onTap: () {
              if (WorkspaceNavigation.isAuthenticated) {
                Go.to(const NotificationsScreen(role: NotificationRole.tenant));
              } else {
                WorkspaceNavigation.open(
                  showLoginSheet: true,
                  detail: () => Go.to(const NotificationsScreen()),
                );
              }
            },
            behavior: HitTestBehavior.opaque,
            child: Container(
              width: 36.r,
              height: 36.r,
              decoration: BoxDecoration(
                color: backgroundColor,
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.sokoonBorder),
              ),
              child: Icon(icon, color: iconColor, size: 18.r),
            ),
          ),
        ),
        if (showBadge)
          PositionedDirectional(
            top: 2.r,
            end: 2.r,
            child: Container(
              width: 8.r,
              height: 8.r,
              decoration: const BoxDecoration(
                color: AppColors.red,
                shape: BoxShape.circle,
              ),
            ),
          ),
      ],
    );
  }
}
