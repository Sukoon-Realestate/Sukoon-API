import 'package:flutter/material.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:sokoun_app/features/chat/presentation/screens/chat_list_screen.dart';
import 'package:sokoun_app/features/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/properties/imports.dart';
import 'package:sokoun_app/features/whats_new/whats_new_service.dart';
import 'package:sokoun_app/features/whats_new/widgets/upgrader_dialog.dart';
import 'package:upgrader/upgrader.dart';

import '../widgets/shared/home_bottom_navigation.dart';
import 'owner_home_screen.dart';
import 'owner_visit_requests_screen.dart';
import 'tenant_home_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.userType});

  final UserType? userType;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final UserType _userType;
  late final List<_HomeTab> _tabs;
  int _currentIndex = 0;

  late final Upgrader upgrader = Upgrader(
    languageCode: Languages.currentLanguage.languageCode,
    // debugDisplayAlways: kDebugMode,
    minAppVersion: RemoteConfigValues.minAppVersion.isEmpty
        ? null
        : RemoteConfigValues.minAppVersion,
    debugLogging: true,
    durationUntilAlertAgain: Duration.zero,
    storeController: UpgraderStoreController(
      onAndroid: () => UpgraderPlayStore(),
      oniOS: () => UpgraderAppStore(),
    ),
  );

  @override
  void initState() {
    super.initState();
    _userType = widget.userType ?? UserTypeHelper.instance.currentUserType;
    _tabs = _userType.isOwner ? _buildOwnerTabs() : _buildTenantTabs();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showLaunchDialogs());
  }

  Future<void> _showLaunchDialogs() async {
    if (!mounted) return;
    await WhatsNewService.showIfNeeded(upgrader: upgrader);
  }

  void _selectTab(int index) {
    if (index == _currentIndex) {
      return;
    }

    setState(() => _currentIndex = index);
  }

  List<_HomeTab> _buildTenantTabs() {
    return [
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.home_outlined,
          selectedIcon: Icons.home_rounded,
          label: LocaleKeys.home,
        ),
        screen: TenantHomeScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.favorite_border_rounded,
          selectedIcon: Icons.favorite_rounded,
          label: LocaleKeys.favoritesNavigationSaved,
        ),
        screen: FavoritesScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.chat_bubble_outline_rounded,
          selectedIcon: Icons.chat_bubble_rounded,
          label: LocaleKeys.chats,
        ),
        screen: ChatListScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.notifications_none_rounded,
          selectedIcon: Icons.notifications_rounded,
          label: LocaleKeys.notifications,
        ),
        screen: NotificationsScreen(role: NotificationRole.tenant),
      ),
    ];
  }

  List<_HomeTab> _buildOwnerTabs() {
    return [
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.home_outlined,
          selectedIcon: Icons.home_rounded,
          label: LocaleKeys.home,
        ),
        screen: OwnerHomeScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.apartment_outlined,
          selectedIcon: Icons.apartment_rounded,
          label: LocaleKeys.notificationsOwnerPropertiesNavigation,
        ),
        screen: OwnerPropertiesScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.assignment_outlined,
          selectedIcon: Icons.assignment_rounded,
          label: LocaleKeys.notificationsOwnerRequestsNavigation,
        ),
        screen: OwnerVisitRequestsScreen(showBackButton: false),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.chat_bubble_outline_rounded,
          selectedIcon: Icons.chat_bubble_rounded,
          label: LocaleKeys.chats,
        ),
        screen: ChatListScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Icons.more_horiz_rounded,
          selectedIcon: Icons.more_horiz_rounded,
          label: LocaleKeys.notificationsOwnerMoreNavigation,
        ),
        screen: OwnerRevenueScreen(showBackButton: false),
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return AppUpgradeAlert(
      upgrader: upgrader,
      onUpdatePressed: upgrader.sendUserToAppStore,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: IndexedStack(
          index: _currentIndex,
          children: _tabs.map((tab) => tab.screen).toList(growable: false),
        ),
        bottomNavigationBar: HomeBottomNavigation(
          destinations: _tabs
              .map((tab) => tab.destination)
              .toList(growable: false),
          currentIndex: _currentIndex,
          onDestinationSelected: _selectTab,
        ),
      ),
    );
  }
}

class _HomeTab {
  const _HomeTab({required this.destination, required this.screen});

  final HomeNavigationDestination destination;
  final Widget screen;
}
