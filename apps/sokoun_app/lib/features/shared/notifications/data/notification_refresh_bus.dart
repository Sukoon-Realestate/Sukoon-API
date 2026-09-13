import 'dart:async';

abstract final class NotificationRefreshBus {
  static final StreamController<void> _controller =
      StreamController<void>.broadcast(sync: true);

  static Stream<void> get stream => _controller.stream;

  static void requestRefresh() => _controller.add(null);
}
