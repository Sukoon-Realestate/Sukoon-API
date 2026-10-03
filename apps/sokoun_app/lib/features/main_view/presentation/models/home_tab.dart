import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_visit_requests_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chats_screen.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import '../../data/enums/app_workspace.dart';
import '../../data/enums/workspace_tab.dart';
import 'home_navigation_destination.dart';

class HomeTab {
  const HomeTab({required this.tab, required this.screen});

  final WorkspaceTab tab;
  final Widget screen;

  HomeNavigationDestination destination({
    required AppWorkspace workspace,
    required int badgeCount,
  }) {
    final Object icon = switch (tab) {
      WorkspaceTab.home => Assets.svg.home.path,
      WorkspaceTab.saved => Icons.favorite_border_rounded,
      WorkspaceTab.messages => Assets.svg.message.path,
      WorkspaceTab.visits || WorkspaceTab.requests => Assets.svg.calendar.path,
      WorkspaceTab.properties => Assets.svg.building.path,
      WorkspaceTab.profile => Assets.svg.profile.path,
    };
    return HomeNavigationDestination(
      icon: icon,
      selectedIcon: tab == WorkspaceTab.saved ? Icons.favorite_rounded : icon,
      label: switch (tab) {
        WorkspaceTab.home => LocaleKeys.home,
        WorkspaceTab.saved => LocaleKeys.favoritesNavigationSaved,
        WorkspaceTab.messages => LocaleKeys.chats,
        WorkspaceTab.visits => LocaleKeys.tenantVisitsTitle,
        WorkspaceTab.requests =>
          LocaleKeys.notificationsOwnerRequestsNavigation,
        WorkspaceTab.properties =>
          LocaleKeys.notificationsOwnerPropertiesNavigation,
        WorkspaceTab.profile => LocaleKeys.profile,
      },
      badgeCount: badgeCount,
    );
  }

  static Map<AppWorkspace, List<HomeTab>> createWorkspaces() {
    const HomeTab messages = HomeTab(
      tab: WorkspaceTab.messages,
      screen: ChatsScreen(),
    );
    return const {
      AppWorkspace.tenant: [
        HomeTab(tab: WorkspaceTab.home, screen: TenantHomeScreen()),
        HomeTab(tab: WorkspaceTab.saved, screen: FavoritesScreen()),
        messages,
        HomeTab(tab: WorkspaceTab.visits, screen: TenantVisitsScreen()),
        HomeTab(
          tab: WorkspaceTab.profile,
          screen: ProfileScreen(workspace: AppWorkspace.tenant),
        ),
      ],
      AppWorkspace.owner: [
        HomeTab(tab: WorkspaceTab.home, screen: OwnerHomeScreen()),
        HomeTab(tab: WorkspaceTab.properties, screen: OwnerPropertiesScreen()),
        HomeTab(
          tab: WorkspaceTab.requests,
          screen: OwnerVisitRequestsScreen(showBackButton: false),
        ),
        messages,
        HomeTab(
          tab: WorkspaceTab.profile,
          screen: ProfileScreen(workspace: AppWorkspace.owner),
        ),
      ],
    };
  }
}
