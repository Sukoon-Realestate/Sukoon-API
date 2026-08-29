import 'package:flutter/material.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_list_screen.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_visit_requests_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/shared/whats_new/whats_new_service.dart';
import 'package:sokoun_app/features/shared/whats_new/widgets/upgrader_dialog.dart';
import 'package:sokoun_app/generated/assets.dart';
import 'package:upgrader/upgrader.dart';

import '../widgets/home_bottom_navigation.dart';

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
    // _tabs = _userType.isOwner ? _buildOwnerTabs() : _buildTenantTabs();
    _tabs = _buildTenantTabs();
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
          icon: Assets.svgHome,
          selectedIcon: Assets.svgHome,
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
          icon: Assets.svgMessage,
          selectedIcon: Assets.svgMessage,
          label: LocaleKeys.chats,
        ),
        screen: ChatListScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgNotification,
          selectedIcon: Assets.svgNotification,
          label: LocaleKeys.notifications,
        ),
        screen: NotificationsScreen(role: NotificationRole.tenant),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgProfile,
          selectedIcon: Assets.svgProfile,
          label: LocaleKeys.profile,
        ),
        screen: const _ProfileTabScreen(),
      ),
    ];
  }

  List<_HomeTab> _buildOwnerTabs() {
    return [
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgHome,
          selectedIcon: Assets.svgHome,
          label: LocaleKeys.home,
        ),
        screen: OwnerHomeScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgBuilding,
          selectedIcon: Assets.svgBuilding,
          label: LocaleKeys.notificationsOwnerPropertiesNavigation,
        ),
        screen: OwnerPropertiesScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgCalendar,
          selectedIcon: Assets.svgCalendar,
          label: LocaleKeys.notificationsOwnerRequestsNavigation,
        ),
        screen: OwnerVisitRequestsScreen(showBackButton: false),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgMessage,
          selectedIcon: Assets.svgMessage,
          label: LocaleKeys.chats,
        ),
        screen: ChatListScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgProfile,
          selectedIcon: Assets.svgProfile,
          label: LocaleKeys.profile,
        ),
        screen: const _ProfileTabScreen(),
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

class _ProfileTabScreen extends StatelessWidget {
  const _ProfileTabScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Center(
          child: Text(
            LocaleKeys.profile,
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
      ),
    );
  }
}
