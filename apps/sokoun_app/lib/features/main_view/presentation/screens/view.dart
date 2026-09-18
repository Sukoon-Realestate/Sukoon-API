import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chats_screen.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_unread_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_unread_cubit.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_visit_requests_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/shared/whats_new/whats_new_service.dart';
import 'package:sokoun_app/features/shared/whats_new/widgets/upgrader_dialog.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_coordinator.dart';
import 'package:sokoun_app/generated/assets.dart';
import 'package:upgrader/upgrader.dart';

import '../widgets/home_bottom_navigation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.userType});

  final UserType? userType;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  late final UserType _userType;
  late final List<_HomeTab> _tabs;
  int _currentIndex = 0;
  late final ChatUnreadCubit _chatUnreadCubit;

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
    WidgetsBinding.instance.addObserver(this);
    _chatUnreadCubit = ChatUnreadCubit();
    _userType = widget.userType ?? UserTypeHelper.instance.currentUserType;
    _tabs = _userType.isOwner ? _buildOwnerTabs() : _buildTenantTabs();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(
        Future.wait<void>([
          NotificationCoordinator.start(),
          _chatUnreadCubit.start(),
          _showLaunchDialogs(),
        ]),
      );
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(_chatUnreadCubit.onAppResumed());
      return;
    }
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached ||
        state == AppLifecycleState.hidden) {
      unawaited(_chatUnreadCubit.onAppBackgrounded());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_chatUnreadCubit.close());
    super.dispose();
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
        screen: const ChatListScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgCalendar,
          selectedIcon: Assets.svgCalendar,
          label: LocaleKeys.tenantVisitsTitle,
        ),
        screen: const TenantVisitsScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgProfile,
          selectedIcon: Assets.svgProfile,
          label: LocaleKeys.profile,
        ),
        screen: const TenantProfileScreen(),
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
        screen: const ChatListScreen(),
      ),
      _HomeTab(
        destination: HomeNavigationDestination(
          icon: Assets.svgProfile,
          selectedIcon: Assets.svgProfile,
          label: LocaleKeys.more,
        ),
        screen: const OwnerMoreScreen(),
      ),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<ChatUnreadCubit>.value(
      value: _chatUnreadCubit,
      child: AppUpgradeAlert(
        upgrader: upgrader,
        onUpdatePressed: upgrader.sendUserToAppStore,
        child: Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: _tabs.map((tab) => tab.screen).toList(growable: false)[_currentIndex],
          bottomNavigationBar:
              BlocSelector<ChatUnreadCubit, AsyncState<ChatUnreadContent>, int>(
                selector: (state) => state.data.count,
                builder: (context, unreadCount) => HomeBottomNavigation(
                  destinations: _tabs
                      .map(
                        (tab) => tab.screen is ChatListScreen
                            ? tab.destination.copyWith(badgeCount: unreadCount)
                            : tab.destination,
                      )
                      .toList(growable: false),
                  currentIndex: _currentIndex,
                  onDestinationSelected: _selectTab,
                ),
              ),
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
