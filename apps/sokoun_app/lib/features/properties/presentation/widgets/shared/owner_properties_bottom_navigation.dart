part of '../../../imports.dart';

enum OwnerPropertiesNavigationTab { home, properties, requests, chat, more }

class OwnerPropertiesBottomNavigation extends StatelessWidget {
  const OwnerPropertiesBottomNavigation({super.key, required this.activeTab});

  final OwnerPropertiesNavigationTab activeTab;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: owner_nav.HomeBottomNav(
        items: [
          owner_nav.HomeBottomNavItemData(
            icon: Icons.home_outlined,
            label: LocaleKeys.home,
            isActive: activeTab == OwnerPropertiesNavigationTab.home,
            onTap: activeTab == OwnerPropertiesNavigationTab.home
                ? null
                : () => Go.off(const OwnerHomeScreen()),
          ),
          owner_nav.HomeBottomNavItemData(
            icon: Icons.apartment_rounded,
            label: LocaleKeys.notificationsOwnerPropertiesNavigation,
            isActive: activeTab == OwnerPropertiesNavigationTab.properties,
            onTap: activeTab == OwnerPropertiesNavigationTab.properties
                ? null
                : () => Go.off(const OwnerPropertiesScreen()),
          ),
          owner_nav.HomeBottomNavItemData(
            icon: Icons.assignment_outlined,
            label: LocaleKeys.notificationsOwnerRequestsNavigation,
            isActive: activeTab == OwnerPropertiesNavigationTab.requests,
            onTap: activeTab == OwnerPropertiesNavigationTab.requests
                ? null
                : () => Go.off(const OwnerVisitRequestsScreen()),
          ),
          owner_nav.HomeBottomNavItemData(
            icon: Icons.chat_bubble_outline_rounded,
            label: LocaleKeys.chats,
            isActive: activeTab == OwnerPropertiesNavigationTab.chat,
            onTap: activeTab == OwnerPropertiesNavigationTab.chat
                ? null
                : () => Go.off(const ChatListScreen()),
          ),
          owner_nav.HomeBottomNavItemData(
            icon: Icons.more_horiz_rounded,
            label: LocaleKeys.notificationsOwnerMoreNavigation,
            isActive: activeTab == OwnerPropertiesNavigationTab.more,
            onTap: activeTab == OwnerPropertiesNavigationTab.more
                ? null
                : () => Go.off(const OwnerRevenueScreen()),
          ),
        ],
      ),
    );
  }
}
