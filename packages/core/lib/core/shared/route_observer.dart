import 'dart:developer';

import 'package:flutter/material.dart';

/// Retains the page identity without changing callers' route arguments.
class AppPageRouteSettings extends RouteSettings {
  const AppPageRouteSettings({required this.page, super.name});
  final Widget page;
}

class AppNavigationObserver extends RouteObserver<ModalRoute<dynamic>> {
  static final AppNavigationObserver instance = AppNavigationObserver._();
  AppNavigationObserver._();

  /// The name (widget runtimeType) of the currently visible route.
  static String? currentRouteName;
  static Route<dynamic>? currentRoute;
  static final List<PageRoute<dynamic>> _pages = [];
  static PageRoute<dynamic>? get currentPageRoute =>
      _pages.isEmpty ? null : _pages.last;
  static Widget? get currentPage {
    final settings = currentPageRoute?.settings;
    return settings is AppPageRouteSettings ? settings.page : null;
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPush(route, previousRoute);
    if (previousRoute == null) _pages.clear();
    if (route is PageRoute<dynamic>) _pages.add(route);
    currentRouteName = route.settings.name;
    currentRoute = route;
    log(
      'onPush -- Route: ${route.settings.name} -- Previous Route: ${previousRoute?.settings.name}',
    );
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
    final index = oldRoute is PageRoute<dynamic>
        ? _pages.indexOf(oldRoute)
        : -1;
    if (index >= 0) {
      if (newRoute is PageRoute<dynamic>) {
        _pages[index] = newRoute;
      } else {
        _pages.removeAt(index);
      }
    } else if (newRoute is PageRoute<dynamic>) {
      _pages.add(newRoute);
    }
    currentRouteName = newRoute?.settings.name;
    currentRoute = newRoute;
    log(
      'didReplace -- Route: ${newRoute?.settings.name} -- Previous Route: ${oldRoute?.settings.name}',
    );
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPop(route, previousRoute);
    _pages.remove(route);
    currentRouteName = previousRoute?.settings.name;
    currentRoute = previousRoute;
    log(
      'didPop -- Route: ${route.settings.name} -- Previous Route: ${previousRoute?.settings.name}',
    );
  }

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didRemove(route, previousRoute);
    _pages.remove(route);
    if (identical(currentRoute, route)) {
      currentRoute = previousRoute;
      currentRouteName = previousRoute?.settings.name;
    }
    log(
      'didRemove -- Route: ${route.settings.name} -- Previous Route: ${previousRoute?.settings.name}',
    );
  }
}
