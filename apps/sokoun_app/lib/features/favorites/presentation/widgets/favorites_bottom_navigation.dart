import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/chat/presentation/screens/chat_list_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/home/presentation/widgets/tenant_widgets/imports.dart';

class FavoritesBottomNavigation extends StatelessWidget {
  const FavoritesBottomNavigation({super.key});

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
            icon: Icons.favorite_rounded,
            label: LocaleKeys.favoritesNavigationSaved,
            isActive: true,
          ),
          HomeBottomNavItemData(
            icon: Icons.chat_bubble_outline_rounded,
            label: LocaleKeys.chats,
            onTap: () => Go.off(const ChatListScreen()),
          ),
          HomeBottomNavItemData(
            icon: Icons.notifications_none_rounded,
            label: LocaleKeys.notifications,
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
