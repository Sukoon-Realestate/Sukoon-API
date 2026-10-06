import 'dart:async';

abstract final class WorkspaceCountsRefreshBus {
  static final StreamController<void> _controller =
      StreamController<void>.broadcast();
  static Stream<void> get stream => _controller.stream;
  static void refresh() => _controller.add(null);
}
