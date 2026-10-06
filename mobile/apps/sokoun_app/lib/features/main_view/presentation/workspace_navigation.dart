import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/register_flow_screen.dart';
import 'package:sokoun_app/shared_widgets/unauthenticated_sheet.dart';
import '../data/enums/app_workspace.dart';
import '../data/enums/workspace_tab.dart';

typedef WorkspaceSelection =
    Future<void> Function(AppWorkspace? workspace, WorkspaceTab? tab);

/// Coordinates authentication, workspace selection and a single pending target.
abstract final class WorkspaceNavigation {
  static WorkspaceSelection? _select;
  static ({AppWorkspace? workspace, WorkspaceTab? tab, VoidCallback? detail})?
  _pending;
  static bool _loginVisible = false;
  static final List<Future<bool> Function()> _leaveGuards = [];

  static void addLeaveGuard(Future<bool> Function() guard) =>
      _leaveGuards.add(guard);
  static void removeLeaveGuard(Future<bool> Function() guard) =>
      _leaveGuards.remove(guard);

  static bool get isAuthenticated =>
      injector.isRegistered<UserCubit>() && UserCubit.instance.isUserLoggedIn;

  static void attach(WorkspaceSelection select) {
    _select = select;
    _loginVisible = false;
  }

  static void detach(WorkspaceSelection select) {
    if (_select == select) _select = null;
  }

  static void clearPending() {
    _pending = null;
    _loginVisible = false;
  }

  static Future<void> resumePending() async {
    if (!isAuthenticated || _select == null) return;
    final target = _pending;
    _pending = null;
    if (target != null) {
      await open(
        workspace: target.workspace,
        tab: target.tab,
        detail: target.detail,
      );
    }
  }

  static Future<void> open({
    AppWorkspace? workspace,
    WorkspaceTab? tab,
    VoidCallback? detail,
    bool showLoginSheet = false,
  }) async {
    if (isAuthenticated && _select == null) {
      _pending = (workspace: workspace, tab: tab, detail: detail);
      return;
    }
    if (!isAuthenticated || _select == null) {
      _pending = (workspace: workspace, tab: tab, detail: detail);
      if (_loginVisible) return;
      _loginVisible = true;
      final UnauthenticatedSheetAction? action = showLoginSheet
          ? await Helpers.showUnAuthSheet<UnauthenticatedSheetAction>()
          : UnauthenticatedSheetAction.login;
      if (action == null) {
        clearPending();
        return;
      }
      final Route<dynamic>? origin = AppNavigationObserver.currentRoute;
      unawaited(
        Go.to<void>(
          action == UnauthenticatedSheetAction.createAccount
              ? const RegisterFlowScreen()
              : const LoginScreen(),
        ).whenComplete(() {
          _loginVisible = false;
          // Preserve signup/login replacements, but discard a cancelled gate.
          if (!isAuthenticated &&
              identical(origin, AppNavigationObserver.currentRoute)) {
            clearPending();
          }
        }),
      );
      return;
    }
    final WorkspaceSelection select = _select!;
    final int generation = AccountSession.generation;
    for (final guard in List.of(_leaveGuards.reversed)) {
      if (!await guard()) return;
    }
    if (!isAuthenticated ||
        _select != select ||
        generation != AccountSession.generation) {
      return;
    }
    if (!await Go.tryBackToInitial()) return;
    if (!isAuthenticated ||
        _select != select ||
        generation != AccountSession.generation) {
      return;
    }
    await select(workspace, tab);
    await WidgetsBinding.instance.endOfFrame;
    if (isAuthenticated &&
        _select == select &&
        generation == AccountSession.generation) {
      detail?.call();
    }
  }
}
