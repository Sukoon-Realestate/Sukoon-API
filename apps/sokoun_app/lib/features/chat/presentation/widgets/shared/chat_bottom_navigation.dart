import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/home/presentation/widgets/tenant_widgets/imports.dart';
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/notifications/presentation/screens/notifications_screen.dart';

class ChatBottomNavigation extends StatelessWidget {
  const ChatBottomNavigation({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: HomeBottomNav(
        items: [
          HomeBottomNavItemData(
            icon: Icons.home_outlined,
            label: LocaleKeys.home,
            onTap: () => Go.off(const TenantHomeScreen()),
          ),
          HomeBottomNavItemData(
            icon: Icons.favorite_border_rounded,
            label: LocaleKeys.favoritesNavigationSaved,
            onTap: () => Go.off(const FavoritesScreen()),
          ),
          HomeBottomNavItemData(
            icon: Icons.chat_bubble_rounded,
            label: LocaleKeys.chats,
            isActive: true,
          ),
          HomeBottomNavItemData(
            icon: Icons.notifications_none_rounded,
            label: LocaleKeys.notifications,
            onTap: () => Go.off(
              const NotificationsScreen(role: NotificationRole.tenant),
            ),
          ),
          HomeBottomNavItemData(
            icon: Icons.person_outline_rounded,
            label: LocaleKeys.favoritesNavigationAccount,
          ),
        ],
      ),
    );
  }
}
