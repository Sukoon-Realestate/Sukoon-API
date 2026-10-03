import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/unread_counts/presentation/cubits/unread_counts_cubit.dart';
import 'package:sokoun_app/features/shared/unread_counts/data/models/unread_counts.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/whats_new/whats_new_service.dart';
import 'package:sokoun_app/features/shared/whats_new/widgets/upgrader_dialog.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_coordinator.dart';
import 'package:sokoun_app/features/shared/permissions/data/enums/device_permission.dart';
import 'package:sokoun_app/features/shared/permissions/presentation/device_permission_flow.dart';
import 'package:upgrader/upgrader.dart';

import '../models/home_tab.dart';
import '../models/home_navigation_destination.dart';
import '../widgets/home_bottom_navigation.dart';
import '../widgets/home_navigation_rail.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/sokoun_content_transition.dart';
import '../../data/enums/app_workspace.dart';
import '../../data/enums/workspace_tab.dart';
import '../cubits/workspace_cubit.dart';
import '../cubits/account_cubit.dart';
import '../workspace_navigation.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  late final WorkspaceCubit _workspaceCubit;
  String? _tabAccountId;
  int _sessionGeneration = AccountSession.generation;
  late final List<HomeTab> _allTabs;
  late final Map<AppWorkspace, List<HomeTab>> _workspaceTabs;
  final Map<AppWorkspace, int> _selectedTabs = {
    AppWorkspace.tenant: 0,
    AppWorkspace.owner: 0,
  };
  final Set<int> _visited = {};
  AppWorkspace get _workspace => _workspaceCubit.state;
  int get _currentIndex => _selectedTabs[_workspace]!;
  List<HomeTab> get _tabs => _workspaceTabs[_workspace]!;
  late final UnreadCountsCubit _countsCubit;
  late final AccountCubit _accountCubit;
  late final Future<void> _accountRequest;

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
    _tabAccountId = _workspaceCubit.userId;
    _countsCubit = UnreadCountsCubit()..watch();
    _accountCubit = AccountCubit()..restoreCachedProfile();
    _accountRequest = _accountCubit.getAccount();
    _workspaceTabs = HomeTab.createWorkspaces();
    _allTabs = _workspaceTabs.values
        .expand((tabs) => tabs)
        .toSet()
        .toList(growable: false);
    WorkspaceNavigation.attach(_applyWorkspace);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      _initializeAccountFeatures();
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (!_hasCurrentSession) return;
    if (state == AppLifecycleState.resumed) {
      _refreshAccount();
      _refreshCounts();
    }
  }

  @override
  void dispose() {
    WorkspaceNavigation.detach(_applyWorkspace);
    WidgetsBinding.instance.removeObserver(this);
    _accountCubit.close();
    _countsCubit.close();
    super.dispose();
  }

  Future<void> _initializeAccountFeatures() async {
    await _accountRequest;
    if (!mounted) return;
    final String? userId = WorkspaceNavigation.isAuthenticated
        ? UserCubit.instance.user.id
        : null;
    // Cookie-only startup can establish an account while the request runs.
    // An ended or replaced signed-in session must not restart home features.
    if (_sessionGeneration != AccountSession.generation &&
        (_tabAccountId != null || userId == null)) {
      return;
    }
    final bool accountChanged = _tabAccountId != userId;
    _tabAccountId = userId;
    _sessionGeneration = AccountSession.generation;
    _workspaceCubit.initialize(userId);
    if (accountChanged) setState(() {});
    await Future.wait<void>([_refreshCounts(), _showLaunchDialogs()]);
  }

  Future<void> _refreshAccount() async {
    if (!_hasCurrentSession || !WorkspaceNavigation.isAuthenticated) {
      return;
    }
    await _accountCubit.getAccount();
  }

  Future<void> _refreshCounts() async {
    if (!_hasCurrentSession) return;
    await _countsCubit.load();
  }

  Future<void> _showLaunchDialogs() async {
    if (!_hasCurrentSession) return;
    await Future.wait<void>([
      WorkspaceNavigation.resumePending(),
      NotificationCoordinator.start(),
    ]);
    if (!mounted ||
        !_hasCurrentSession ||
        ModalRoute.of(context)?.isCurrent != true) {
      return;
    }
    await WhatsNewService.showIfNeeded(upgrader: upgrader);
    if (!mounted ||
        !_hasCurrentSession ||
        !WorkspaceNavigation.isAuthenticated) {
      return;
    }
    await DevicePermissionFlow.ensureGranted(
      context,
      DevicePermission.notifications,
      promptOnce: true,
    );
  }

  Future<void> _selectTab(int index) async {
    if (!_hasCurrentSession) return;
    if (index == _currentIndex) {
      return;
    }

    if (index != 0 && !WorkspaceNavigation.isAuthenticated) {
      await WorkspaceNavigation.open(
        workspace: _workspace,
        tab: _tabs[index].tab,
        showLoginSheet: true,
      );
      return;
    }
    setState(() => _selectedTabs[_workspace] = index);
  }

  Future<void> _applyWorkspace(
    AppWorkspace? workspace,
    WorkspaceTab? tab,
  ) async {
    if (!_hasCurrentSession) return;
    final AppWorkspace target = workspace ?? _workspace;
    if (tab != null) {
      final int index = _workspaceTabs[target]!.indexWhere(
        (destination) => destination.tab == tab,
      );
      if (index >= 0) _selectedTabs[target] = index;
    }
    await _workspaceCubit.switchTo(target);
    if (_hasCurrentSession) {
      setState(() {});
    }
  }

  bool get _hasCurrentSession =>
      mounted && _sessionGeneration == AccountSession.generation;

  List<HomeNavigationDestination> _navigationDestinations({
    required int unreadCount,
  }) => _tabs
      .map((tab) {
        final int badgeCount = switch (tab.tab) {
          WorkspaceTab.messages => unreadCount,
          _ => 0,
        };
        return tab.destination(workspace: _workspace, badgeCount: badgeCount);
      })
      .toList(growable: false);

  Widget _buildNavigation({required bool rail}) =>
      BlocSelector<UnreadCountsCubit, AsyncState<UnreadCounts>, UnreadCounts>(
        selector: (state) => state.data,
        builder: (context, counts) {
          final destinations = _navigationDestinations(
            unreadCount: counts.chatCount,
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
      );

  @override
  Widget build(BuildContext context) {
    context.locale;
    return MultiBlocProvider(
      providers: [
        BlocProvider<WorkspaceCubit>.value(value: _workspaceCubit),
        BlocProvider<UnreadCountsCubit>.value(value: _countsCubit),
        BlocProvider<AccountCubit>.value(value: _accountCubit),
      ],
      child: BlocBuilder<WorkspaceCubit, AppWorkspace>(
        builder: (context, workspace) {
          // The workspace reset can arrive before the signed-out route is disposed.
          if (!_hasCurrentSession) return const SizedBox.shrink();

          final int bodyIndex = _allTabs.indexOf(
            _workspaceTabs[workspace]![_selectedTabs[workspace]!],
          );
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
                            // Keep visited tabs alive within the current session.
                            key: ValueKey(_tabAccountId),
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
