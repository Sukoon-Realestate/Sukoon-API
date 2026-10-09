import 'package:flutter/widgets.dart';
import '../data/models/app_destination.dart';

/// Route-owned identities for screens whose selected resource can change.
abstract final class VisibleDestinationRegistry {
  static final Map<Route<dynamic>, AppDestination Function()> _readers = {};

  static VoidCallback bind(
    Route<dynamic> route,
    AppDestination Function() read,
  ) {
    _readers[route] = read;
    return () {
      if (identical(_readers[route], read)) _readers.remove(route);
    };
  }

  static AppDestination? read(Route<dynamic>? route) => _readers[route]?.call();
}
