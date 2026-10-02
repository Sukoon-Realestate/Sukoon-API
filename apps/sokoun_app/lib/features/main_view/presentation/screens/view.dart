import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/features/shared/unread_counts/presentation/cubits/unread_counts_cubit.dart';
import 'package:sokoun_app/features/shared/unread_counts/data/models/unread_counts.dart';
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
import 'package:upgrader/upgrader.dart';

import '../widgets/home_bottom_navigation.dart';
import '../widgets/home_navigation_rail.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/sokoun_content_transition.dart';
import '../../data/enums/app_workspace.dart';
import '../../data/enums/workspace_tab.dart';
import '../cubits/workspace_cubit.dart';
import '../cubits/account_cubit.dart';
import '../../data/models/workspace_counts.dart';
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
  late final UnreadCountsCubit _unreadCountsCubit;
  late final ChatUnreadCubit _chatUnreadCubit;
  late final TenantProfileCubit _tenantProfileCubit;
  late final AccountCubit _accountCubit;
  late final Future<void> _accountRequest;
  late final UnreadCountsCubit _ownerCounts;

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
    _unreadCountsCubit = UnreadCountsCubit()..watch();
    _chatUnreadCubit = ChatUnreadCubit(unreadCounts: _unreadCountsCubit);
    _ownerCounts = UnreadCountsCubit(workspace: AppWorkspace.owner)..watch();
    _tenantProfileCubit = TenantProfileCubit();
    if (WorkspaceNavigation.isAuthenticated) {
      _tenantProfileCubit.restoreCachedProfile();
    }
    _accountCubit = AccountCubit();
    _accountRequest = _accountCubit.getAccount(
      onProfileLoaded: _tenantProfileCubit.setProfile,
    );
    _tenantProfileCubit.useAccountRequest(_accountRequest);
    final List<_HomeTab> ownerTabs = _buildOwnerTabs();
    _allTabs = [
      ..._buildTenantTabs(),
      ...ownerTabs..removeAt(3),
      // ownerTabs[0],
      // ownerTabs[1],
      // ownerTabs[2],
      // ownerTabs[4],
    ];
    WorkspaceNavigation.attach(_applyWorkspace);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      unawaited(_initializeAccountFeatures());
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(_chatUnreadCubit.onAppResumed());
      unawaited(_refreshTenantProfile());
      unawaited(_refreshCounts());
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
    unawaited(_tenantProfileCubit.close());
    unawaited(_accountCubit.close());
    unawaited(_ownerCounts.close());
    unawaited(_unreadCountsCubit.close());
    super.dispose();
  }

  Future<void> _initializeAccountFeatures() async {
    await _accountRequest;
    if (!mounted) return;
    final String? userId = WorkspaceNavigation.isAuthenticated
        ? UserCubit.instance.user.id
        : null;
    final bool accountChanged = _workspaceCubit.userId != userId;
    _workspaceCubit.initialize(userId);
    if (accountChanged) setState(() {});
    await Future.wait<void>([
      _chatUnreadCubit.start(),
      _refreshCounts(),
      _showLaunchDialogs(),
    ]);
  }

  Future<void> _refreshTenantProfile() async {
    if (!_workspace.isTenant || !WorkspaceNavigation.isAuthenticated) return;
    await _tenantProfileCubit.getProfile();
  }

  Future<void> _refreshCounts() async {
    await Future.wait([_unreadCountsCubit.load(), _ownerCounts.load()]);
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
    if (mounted) {
      setState(() {});
    }
  }

  List<HomeNavigationDestination> _navigationDestinations({
    required int unreadCount,
    required WorkspaceCounts counts,
    required int reviewsCount,
  }) => _tabs
      .map((tab) {
        final int badgeCount = switch (tab.tab) {
          WorkspaceTab.messages => unreadCount,
          WorkspaceTab.saved when _workspace.isTenant => counts.favorites,
          WorkspaceTab.visits when _workspace.isTenant => counts.visits,
          WorkspaceTab.requests when _workspace.isOwner => counts.visits,
          WorkspaceTab.profile when _workspace.isTenant => reviewsCount,
          _ => 0,
        };
        return tab.destination.copyWith(badgeCount: badgeCount);
      })
      .toList(growable: false);

  List<_HomeTab> _buildTenantTabs() {
    return [
      _HomeTab(
        tab: WorkspaceTab.home,
        destination: HomeNavigationDestination(
          icon: Assets.svg.home.path,
          selectedIcon: Assets.svg.home.path,
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
          icon: Assets.svg.message.path,
          selectedIcon: Assets.svg.message.path,
          label: LocaleKeys.chats,
        ),
        screen: const ChatListScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.visits,
        destination: HomeNavigationDestination(
          icon: Assets.svg.calendar.path,
          selectedIcon: Assets.svg.calendar.path,
          label: LocaleKeys.tenantVisitsTitle,
        ),
        screen: const TenantVisitsScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.profile,
        destination: HomeNavigationDestination(
          icon: Assets.svg.profile.path,
          selectedIcon: Assets.svg.profile.path,
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
          icon: Assets.svg.home.path,
          selectedIcon: Assets.svg.home.path,
          label: LocaleKeys.home,
        ),
        screen: const OwnerHomeScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.properties,
        destination: HomeNavigationDestination(
          icon: Assets.svg.building.path,
          selectedIcon: Assets.svg.building.path,
          label: LocaleKeys.notificationsOwnerPropertiesNavigation,
        ),
        screen: const OwnerPropertiesScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.requests,
        destination: HomeNavigationDestination(
          icon: Assets.svg.calendar.path,
          selectedIcon: Assets.svg.calendar.path,
          label: LocaleKeys.notificationsOwnerRequestsNavigation,
        ),
        screen: const OwnerVisitRequestsScreen(showBackButton: false),
      ),
      _HomeTab(
        tab: WorkspaceTab.messages,
        destination: HomeNavigationDestination(
          icon: Assets.svg.message.path,
          selectedIcon: Assets.svg.message.path,
          label: LocaleKeys.chats,
        ),
        screen: const ChatListScreen(),
      ),
      _HomeTab(
        tab: WorkspaceTab.profile,
        destination: HomeNavigationDestination(
          icon: Assets.svg.profile.path,
          selectedIcon: Assets.svg.profile.path,
          label: LocaleKeys.more,
        ),
        screen: const OwnerMoreScreen(),
      ),
    ];
  }

  Widget _buildNavigation({required bool rail}) =>
      BlocSelector<ChatUnreadCubit, AsyncState<ChatUnreadContent>, int>(
        selector: (state) => state.data.count,
        builder: (context, unreadCount) =>
            BlocSelector<
              UnreadCountsCubit,
              AsyncState<UnreadCounts>,
              WorkspaceCounts
            >(
              bloc: _workspace.isOwner ? _ownerCounts : _unreadCountsCubit,
              selector: (state) => state.data.workspace,
              builder: (context, counts) {
                final destinations = _navigationDestinations(
                  unreadCount: unreadCount,
                  counts: counts,
                  reviewsCount: context.select<TenantProfileCubit, int>(
                    (cubit) => cubit.data.stats.reviewsCount,
                  ),
                );
                return rail
                    ? HomeNavigationRail(
                        destinations: destinations,
                        currentIndex: _currentIndex,
                        onDestinationSelected: _selectTab,
                      )
                    : HomeBottomNavigation(
                        destinations: destinations,
                        currentIndex: _currentIndex,
                        onDestinationSelected: _selectTab,
                      );
              },
            ),
      );

  @override
  Widget build(BuildContext context) {
    context.locale;
    return MultiBlocProvider(
      providers: [
        BlocProvider<WorkspaceCubit>.value(value: _workspaceCubit),
        BlocProvider<UnreadCountsCubit>.value(value: _unreadCountsCubit),
        BlocProvider<ChatUnreadCubit>.value(value: _chatUnreadCubit),
        BlocProvider<TenantProfileCubit>.value(value: _tenantProfileCubit),
      ],
      child: BlocBuilder<WorkspaceCubit, AppWorkspace>(
        builder: (context, workspace) {
          final int bodyIndex = _tabIndices[workspace]![_currentIndex];
          _visited.add(bodyIndex);
          return AppUpgradeAlert(
            upgrader: upgrader,
            onUpdatePressed: upgrader.sendUserToAppStore,
            child: LayoutBuilder(
              builder: (context, constraints) {
                final bool rail =
                    constraints.maxWidth >= SokounLayout.navigationBreakpoint;
                return Scaffold(
                  backgroundColor: AppColors.scaffoldBackground,
                  body: Row(
                    children: [
                      SizedBox(
                        width: rail ? 104 : 0,
                        child: rail ? _buildNavigation(rail: true) : null,
                      ),
                      Expanded(
                        child: SokounContentTransition(
                          identity: bodyIndex,
                          child: IndexedStack(
                            // Account identity, not window size, owns tab lifetimes.
                            key: ValueKey(_workspaceCubit.userId),
                            index: bodyIndex,
                            children: List<Widget>.generate(
                              _allTabs.length,
                              (index) => TickerMode(
                                enabled: index == bodyIndex,
                                child: _visited.contains(index)
                                    ? _allTabs[index].screen
                                    : const SizedBox.shrink(),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  bottomNavigationBar: rail
                      ? null
                      : _buildNavigation(rail: false),
                );
              },
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
