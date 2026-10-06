import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppLifecycleManager extends StatefulWidget {
  final Widget child;
  final Function(AppLifecycleState state)? onStateChanged;
  final VoidCallback? onResumed; // App is in the foreground and interactive.
  final VoidCallback? onPaused; // in background
  final VoidCallback? onInactive; // 	App is in an inactive state (e.g. a phone call overlay). Not receiving user input.
  final VoidCallback? onDetached; // rarely used
  final VoidCallback? onHidden; // in ios

  const AppLifecycleManager({
    super.key,
    required this.child,
    this.onStateChanged,
    this.onResumed,
    this.onPaused,
    this.onInactive,
    this.onDetached,
    this.onHidden,
  });

  @override
  State<AppLifecycleManager> createState() => _AppLifecycleManagerState();
}

class _AppLifecycleManagerState extends State<AppLifecycleManager>
    with WidgetsBindingObserver {
  AppLifecycleState? _lastLifecycleState;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _lastLifecycleState = WidgetsBinding.instance.lifecycleState;
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }


  void _handleAppResumed() {
    debugPrint('App is in FOREGROUND (resumed)');
    widget.onResumed?.call();
    // Add your foreground logic here
    // Example: Resume timers, refresh data, etc.
  }

  void _handleAppPaused() {
    debugPrint('App is in BACKGROUND (paused)');
    widget.onPaused?.call();
    // Add your background logic here
    // Example: Pause timers, save state, etc.
  }

  void _handleAppInactive() {
    debugPrint('App is INACTIVE');
    widget.onInactive?.call();
    // App is inactive (e.g., during phone call, system dialog)
  }

  void _handleAppDetached() {
    debugPrint('App is DETACHED (about to be terminated)');
    widget.onDetached?.call();
    // App is about to be terminated
    // Save critical data here
  }

  void _handleAppHidden() {
    debugPrint('App is HIDDEN');
    widget.onHidden?.call();
    // App is hidden (iOS specific)
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    widget.onStateChanged?.call(state);

    switch (state) {
      case AppLifecycleState.resumed:
        _handleAppResumed();
        break;
      case AppLifecycleState.paused:
        _handleAppPaused();
        break;
      case AppLifecycleState.inactive:
        _handleAppInactive();
        break;
      case AppLifecycleState.detached:
        _handleAppDetached();
        break;
      case AppLifecycleState.hidden:
        _handleAppHidden();
        break;
    }

    _lastLifecycleState = state;

    // Log state change for debugging
    debugPrint('App lifecycle state changed: ${state.name}');
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}

// Service class for handling app lifecycle globally
class AppLifecycleService {
  static final AppLifecycleService _instance = AppLifecycleService._internal();
  factory AppLifecycleService() => _instance;
  AppLifecycleService._internal();

  AppLifecycleState? _currentState;

  AppLifecycleState? get currentState => _currentState;

  bool get isInForeground => _currentState == AppLifecycleState.resumed;
  bool get isInBackground => _currentState == AppLifecycleState.paused;
  bool get isInactive => _currentState == AppLifecycleState.inactive;
  bool get isDetached => _currentState == AppLifecycleState.detached;
  bool get isHidden => _currentState == AppLifecycleState.hidden;
}
