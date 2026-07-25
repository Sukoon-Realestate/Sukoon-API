part of '../../../imports.dart';

class TenantVisitsBottomNavigation extends StatelessWidget {
  const TenantVisitsBottomNavigation({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: tenant_nav.HomeBottomNav(
        items: [
          tenant_nav.HomeBottomNavItemData(
            icon: Icons.home_outlined,
            label: LocaleKeys.home,
            isActive: true,
            onTap: () => Go.off(const TenantHomeScreen()),
          ),
          tenant_nav.HomeBottomNavItemData(
            icon: Icons.favorite_border_rounded,
            label: LocaleKeys.favoritesNavigationSaved,
            onTap: () => Go.off(const FavoritesScreen()),
          ),
          tenant_nav.HomeBottomNavItemData(
            icon: Icons.chat_bubble_outline_rounded,
            label: LocaleKeys.chats,
            onTap: () => Go.off(const ChatListScreen()),
          ),
          tenant_nav.HomeBottomNavItemData(
            icon: Icons.notifications_none_rounded,
            label: LocaleKeys.notifications,
            onTap: () => Go.off(
              const NotificationsScreen(role: NotificationRole.tenant),
            ),
          ),
          tenant_nav.HomeBottomNavItemData(
            icon: Icons.person_outline_rounded,
            label: LocaleKeys.favoritesNavigationAccount,
          ),
        ],
      ),
    );
  }
}
