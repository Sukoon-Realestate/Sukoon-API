import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/chat/presentation/screens/chat_list_screen.dart';
import 'package:sokoun_app/features/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/owner_listings_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/owner_requests_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/home/presentation/widgets/owner_widgets/home_bottom_nav.dart'
    as owner_nav;
import 'package:sokoun_app/features/home/presentation/widgets/tenant_widgets/home_bottom_nav.dart'
    as tenant_nav;
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';

class NotificationBottomNavigation extends StatelessWidget {
  const NotificationBottomNavigation({super.key, required this.role});

  final NotificationRole role;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: role.isOwner ? _ownerNavigation : _tenantNavigation,
    );
  }

  Widget get _tenantNavigation {
    return tenant_nav.HomeBottomNav(
      items: [
        tenant_nav.HomeBottomNavItemData(
          icon: Icons.home_outlined,
          label: LocaleKeys.home,
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
          icon: Icons.notifications_rounded,
          label: LocaleKeys.notifications,
          isActive: true,
        ),
        tenant_nav.HomeBottomNavItemData(
          icon: Icons.person_outline_rounded,
          label: LocaleKeys.favoritesNavigationAccount,
        ),
      ],
    );
  }

  Widget get _ownerNavigation {
    return owner_nav.HomeBottomNav(
      items: [
        owner_nav.HomeBottomNavItemData(
          icon: Icons.home_outlined,
          label: LocaleKeys.home,
          isActive: true,
          onTap: () => Go.off(const OwnerHomeScreen()),
        ),
        owner_nav.HomeBottomNavItemData(
          icon: Icons.apartment_rounded,
          label: LocaleKeys.notificationsOwnerPropertiesNavigation,
          onTap: () => Go.off(const OwnerListingsScreen()),
        ),
        owner_nav.HomeBottomNavItemData(
          icon: Icons.assignment_outlined,
          label: LocaleKeys.notificationsOwnerRequestsNavigation,
          onTap: () => Go.off(const OwnerRequestsScreen()),
        ),
        owner_nav.HomeBottomNavItemData(
          icon: Icons.chat_bubble_outline_rounded,
          label: LocaleKeys.chats,
          onTap: () => Go.off(const ChatListScreen()),
        ),
        owner_nav.HomeBottomNavItemData(
          icon: Icons.more_horiz_rounded,
          label: LocaleKeys.notificationsOwnerMoreNavigation,
        ),
      ],
    );
  }
}
