import 'dart:async';

import 'package:flutter/material.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/route_observer.dart';

import '../../../notifications/data/enums/app_notification_kind.dart';
import '../../../notifications/data/foreground_notification_bus.dart';
import '../../../notifications/data/models/app_notification_content.dart';

/// Refreshes contact permissions when another device accepts a visit, or when
/// returning from a visit flow. The screen's existing Cubit owns the request.
class VisitContactRefresh extends StatefulWidget {
  const VisitContactRefresh({
    super.key,
    required this.onRefresh,
    required this.child,
    this.visitId = '',
    this.propertyId = '',
    this.refreshOnReturn = false,
  });

  final String visitId;
  final String propertyId;
  final bool refreshOnReturn;
  final Future<void> Function() onRefresh;
  final Widget child;

  @override
  State<VisitContactRefresh> createState() => _VisitContactRefreshState();
}

class _VisitContactRefreshState extends State<VisitContactRefresh>
    with WidgetsBindingObserver, RouteAware {
  final int _sessionGeneration = AccountSession.generation;
  StreamSubscription<AppNotificationContent>? _subscription;
  ModalRoute<dynamic>? _route;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _subscription = ForegroundNotificationBus.stream.listen((notification) {
      if (notification.kind != AppNotificationKind.visitAccepted) return;
      final payload = notification.payload;
      if ((widget.visitId.isNotEmpty && payload.visitId == widget.visitId) ||
          (widget.propertyId.isNotEmpty &&
              payload.propertyId == widget.propertyId)) {
        _refresh();
      }
    });
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final route = ModalRoute.of(context);
    if (identical(_route, route)) return;
    AppNavigationObserver.instance.unsubscribe(this);
    _route = route;
    if (route != null) AppNavigationObserver.instance.subscribe(this, route);
  }

  void _refresh() {
    if (!mounted || _sessionGeneration != AccountSession.generation) return;
    unawaited(widget.onRefresh());
  }

  @override
  void didPopNext() {
    if (widget.refreshOnReturn) _refresh();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _refresh();
  }

  @override
  void dispose() {
    _subscription?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    AppNavigationObserver.instance.unsubscribe(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
