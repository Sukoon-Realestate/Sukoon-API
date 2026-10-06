import 'dart:async';
import 'package:flutter/material.dart';

enum InternetStatus{
  online,
  offline,
  slow,
}

extension InternetStatusExtension on InternetStatus{
  bool get isOnline => this == InternetStatus.online;
  bool get isOffline => this == InternetStatus.offline;

}

abstract class InternetInterceptorWidget extends StatelessWidget {
  final StreamController<InternetStatus> internetStreamController = StreamController<InternetStatus>();

  final Widget? loadingWidget;
  final FutureOr<void> Function(InternetStatus connectionStatus) onChanged;
  final Widget Function(InternetStatus connectionStatus) builder;
  final Widget Function(InternetStatus connectionStatus)? onInitialStatusBuilder;

  InternetInterceptorWidget({super.key,
    this.loadingWidget,
    this.onInitialStatusBuilder,
    required this.onChanged,
    required this.builder,
  });

  @override
  Widget build(BuildContext context);
}
