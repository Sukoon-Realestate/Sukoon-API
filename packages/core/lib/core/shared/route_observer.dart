import 'dart:developer';

import 'package:flutter/material.dart';

class AppNavigationObserver extends RouteObserver<ModalRoute<dynamic>> {
  static final AppNavigationObserver instance = AppNavigationObserver._();
  AppNavigationObserver._();

  /// The name (widget runtimeType) of the currently visible route.
  static String? currentRouteName;
  static Route<dynamic>? currentRoute;

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPush(route, previousRoute);
    currentRouteName = route.settings.name;
    currentRoute = route;
    log(
      'onPush -- Route: ${route.settings.name} -- Previous Route: ${previousRoute?.settings.name}',
    );
  }

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    super.didReplace(newRoute: newRoute, oldRoute: oldRoute);
    currentRouteName = newRoute?.settings.name;
    currentRoute = newRoute;
    log(
      'didReplace -- Route: ${newRoute?.settings.name} -- Previous Route: ${oldRoute?.settings.name}',
    );
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPop(route, previousRoute);
    currentRouteName = previousRoute?.settings.name;
    currentRoute = previousRoute;
    log(
      'didPop -- Route: ${route.settings.name} -- Previous Route: ${previousRoute?.settings.name}',
    );
  }

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didRemove(route, previousRoute);
    if (identical(currentRoute, route)) {
      currentRoute = previousRoute;
      currentRouteName = previousRoute?.settings.name;
    }
    log(
      'didRemove -- Route: ${route.settings.name} -- Previous Route: ${previousRoute?.settings.name}',
    );
  }
}
