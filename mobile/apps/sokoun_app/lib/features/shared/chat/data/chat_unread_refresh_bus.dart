import 'dart:async';

abstract final class ChatUnreadRefreshBus {
  static final StreamController<int> _controller =
      StreamController<int>.broadcast(sync: true);

  static Stream<int> get stream => _controller.stream;

  static void requestRefresh({int removedUnreadCount = 0}) =>
      _controller.add(removedUnreadCount);
}
