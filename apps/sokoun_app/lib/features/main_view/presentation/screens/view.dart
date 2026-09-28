import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
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
import 'package:sokoun_app/features/shared/permissions/data/enums/device_permission.dart';
import 'package:sokoun_app/features/shared/permissions/presentation/device_permission_flow.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/cubits/unread_notifications_cubit.dart';
import 'package:sokoun_app/generated/assets.dart';
import 'package:upgrader/upgrader.dart';

import '../widgets/home_bottom_navigation.dart';
import '../../data/enums/app_workspace.dart';
import '../../data/enums/workspace_tab.dart';
import '../cubits/workspace_cubit.dart';
import '../workspace_navigation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  late final WorkspaceCubit _workspaceCubit;
  late final List<_HomeTab> _allTabs;
  final Map<AppWorkspace, int> _selectedTabs = {
    AppWorkspace.tenant: 0,
    AppWorkspace.owner: 0,
  };
  final Set<int> _visited = {};
  static const Map<AppWorkspace, List<int>> _tabIndices = {
    AppWorkspace.tenant: [0, 1, 2, 3, 4],
    AppWorkspace.owner: [5, 6, 7, 2, 8],
  };
  AppWorkspace get _workspace => _workspaceCubit.state;
  int get _currentIndex => _selectedTabs[_workspace]!;
  List<_HomeTab> get _tabs => _tabIndices[_workspace]!
      .map((index) => _allTabs[index])
      .toList(growable: false);
  late final ChatUnreadCubit _chatUnreadCubit;
  late final UnreadNotificationsCubit _notificationUnreadCubit;

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
    if (!injector.isRegistered<WorkspaceCubit>()) {
      injector.registerSingleton<WorkspaceCubit>(WorkspaceCubit());
    }
    _workspaceCubit = WorkspaceCubit.instance;
    _workspaceCubit.initialize(
      WorkspaceNavigation.isAuthenticated ? UserCubit.instance.user.id : null,
    );
    _chatUnreadCubit = ChatUnreadCubit();
    _notificationUnreadCubit = UnreadNotificationsCubit()
      ..watchRefreshRequests();
    final List<_HomeTab> ownerTabs = _buildOwnerTabs();
    _allTabs = [
      ..._buildTenantTabs(),
      ownerTabs[0],
      ownerTabs[1],
      ownerTabs[2],
      ownerTabs[4],
    ];
    WorkspaceNavigation.attach(_applyWorkspace);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      unawaited(
        Future.wait<void>([
          _chatUnreadCubit.start(),
          _notificationUnreadCubit.loadUnreadCount(),
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
    WorkspaceNavigation.detach(_applyWorkspace);
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_chatUnreadCubit.close());
    unawaited(_notificationUnreadCubit.close());
    super.dispose();
  }

  Future<void> _showLaunchDialogs() async {
    await Future.wait<void>([
      WorkspaceNavigation.resumePending(),
      NotificationCoordinator.start(),
    ]);
    if (!mounted || ModalRoute.of(context)?.isCurrent != true) return;
    await WhatsNewService.showIfNeeded(upgrader: upgrader);
    if (!mounted || !WorkspaceNavigation.isAuthenticated) return;
    await DevicePermissionFlow.ensureGranted(
      context,
      DevicePermission.notifications,
      promptOnce: true,
    );
  }

  void _selectTab(int index) {
    if (index == _currentIndex) {
      return;
    }

    if (index != 0 && !WorkspaceNavigation.isAuthenticated) {
      unawaited(
        WorkspaceNavigation.open(
          workspace: _workspace,
          tab: _tabs[index].tab,
          showLoginSheet: true,
        ),
      );
      return;
    }
    setState(() => _selectedTabs[_workspace] = index);
  }

  Future<void> _applyWorkspace(
    AppWorkspace? workspace,
    WorkspaceTab? tab,
  ) async {
    if (!mounted) return;
    final AppWorkspace target = workspace ?? _workspace;
    if (tab != null) {
      final int index = _tabIndices[target]!.indexWhere(
        (index) => _allTabs[index].tab == tab,
      );
      if (index >= 0) _selectedTabs[target] = index;
    }
    await _workspaceCubit.switchTo(target);
    if (mounted) setState(() {});
  }

  List<_HomeTab> _buildTenantTabs() {
    return [
      _HomeTab(
        tab: WorkspaceTab.home,
        destination: HomeNavigationDestination(
          icon: Assets.svgHome,
          selectedIcon: Assets.svgHome,
          label: LocaleKeys.home,
        ),
        screen: TenantHomeScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.saved,
        destination: HomeNavigationDestination(
          icon: Icons.favorite_border_rounded,
          selectedIcon: Icons.favorite_rounded,
          label: LocaleKeys.favoritesNavigationSaved,
        ),
        screen: FavoritesScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.messages,
        destination: HomeNavigationDestination(
          icon: Assets.svgMessage,
          selectedIcon: Assets.svgMessage,
          label: LocaleKeys.chats,
        ),
        screen: const ChatListScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.visits,
        destination: HomeNavigationDestination(
          icon: Assets.svgCalendar,
          selectedIcon: Assets.svgCalendar,
          label: LocaleKeys.tenantVisitsTitle,
        ),
        screen: const TenantVisitsScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.profile,
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
        tab: WorkspaceTab.home,
        destination: HomeNavigationDestination(
          icon: Assets.svgHome,
          selectedIcon: Assets.svgHome,
          label: LocaleKeys.home,
        ),
        screen: const OwnerHomeScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.properties,
        destination: HomeNavigationDestination(
          icon: Assets.svgBuilding,
          selectedIcon: Assets.svgBuilding,
          label: LocaleKeys.notificationsOwnerPropertiesNavigation,
        ),
        screen: const OwnerPropertiesScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.requests,
        destination: HomeNavigationDestination(
          icon: Assets.svgCalendar,
          selectedIcon: Assets.svgCalendar,
          label: LocaleKeys.notificationsOwnerRequestsNavigation,
        ),
        screen: const OwnerVisitRequestsScreen(showBackButton: false),
      ),
      _HomeTab(
        tab: WorkspaceTab.messages,
        destination: HomeNavigationDestination(
          icon: Assets.svgMessage,
          selectedIcon: Assets.svgMessage,
          label: LocaleKeys.chats,
        ),
        screen: const ChatListScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.profile,
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
    return MultiBlocProvider(
      providers: [
        BlocProvider<WorkspaceCubit>.value(value: _workspaceCubit),
        BlocProvider<ChatUnreadCubit>.value(value: _chatUnreadCubit),
        BlocProvider<UnreadNotificationsCubit>.value(
          value: _notificationUnreadCubit,
        ),
      ],
      child: BlocBuilder<WorkspaceCubit, AppWorkspace>(
        builder: (context, workspace) {
          final int bodyIndex = _tabIndices[workspace]![_currentIndex];
          _visited.add(bodyIndex);
          return AppUpgradeAlert(
            upgrader: upgrader,
            onUpdatePressed: upgrader.sendUserToAppStore,
            child: Scaffold(
              backgroundColor: AppColors.scaffoldBackground,
              body: IndexedStack(
                index: bodyIndex,
                children: List<Widget>.generate(
                  _allTabs.length,
                  (index) => _visited.contains(index)
                      ? _allTabs[index].screen
                      : const SizedBox.shrink(),
                ),
              ),
              bottomNavigationBar:
                  BlocSelector<
                    ChatUnreadCubit,
                    AsyncState<ChatUnreadContent>,
                    int
                  >(
                    selector: (state) => state.data.count,
                    builder: (context, unreadCount) => HomeBottomNavigation(
                      destinations: _tabs
                          .map(
                            (tab) => tab.screen is ChatListScreen
                                ? tab.destination.copyWith(
                                    badgeCount: unreadCount,
                                  )
                                : tab.destination,
                          )
                          .toList(growable: false),
                      currentIndex: _currentIndex,
                      onDestinationSelected: _selectTab,
                    ),
                  ),
            ),
          );
        },
      ),
    );
  }
}

class _HomeTab {
  const _HomeTab({
    required this.tab,
    required this.destination,
    required this.screen,
  });

  final WorkspaceTab tab;
  final HomeNavigationDestination destination;
  final Widget screen;
}
