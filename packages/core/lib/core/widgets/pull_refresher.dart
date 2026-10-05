import 'package:flutter/material.dart';

import '../../config/res/config_imports.dart';
import 'pull_refresher_theme.dart';

class PullRefresherWidget extends StatefulWidget {
  final Widget child;
  final Future<void> Function() onRefresh;

  const PullRefresherWidget({
    super.key,
    required this.child,
    required this.onRefresh,
  });

  @override
  State<PullRefresherWidget> createState() => _PullRefresherWidgetState();
}

class _PullRefresherWidgetState extends State<PullRefresherWidget> {
  final ValueNotifier<RefreshIndicatorStatus?> _status = ValueNotifier(null);
  RefreshIndicatorStatus? _gestureStatus;

  void _onStatusChange(RefreshIndicatorStatus? status) {
    if (!mounted) return;
    _gestureStatus = status;
    // Flutter enters drag before it knows which direction the user will pull.
    _status.value = status == RefreshIndicatorStatus.drag ? null : status;
  }

  bool _onScrollNotification(ScrollNotification notification) {
    if (notification.depth != 0 ||
        _gestureStatus != RefreshIndicatorStatus.drag) {
      return false;
    }
    final metrics = notification.metrics;
    final bool reversed = metrics.axisDirection == AxisDirection.up;
    if (notification is OverscrollNotification) {
      final bool pulling = reversed
          ? notification.overscroll > 0
          : notification.overscroll < 0;
      _status.value = pulling ? RefreshIndicatorStatus.drag : null;
    } else if (notification is ScrollUpdateNotification) {
      final bool pulling = reversed
          ? metrics.pixels > metrics.maxScrollExtent
          : metrics.pixels < metrics.minScrollExtent;
      _status.value = pulling ? RefreshIndicatorStatus.drag : null;
    }
    return false;
  }

  Future<void> _refresh() async {
    // Some Flutter versions do not notify the transition from snap to refresh.
    _onStatusChange(RefreshIndicatorStatus.refresh);
    try {
      await widget.onRefresh();
    } finally {
      _onStatusChange(RefreshIndicatorStatus.done);
    }
  }

  @override
  void dispose() {
    _status.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).extension<PullRefresherTheme>();
    final content = ScrollConfiguration(
      behavior: ScrollConfiguration.of(context).copyWith(
        physics: AlwaysScrollableScrollPhysics(
          parent: ScrollConfiguration.of(context).getScrollPhysics(context),
        ),
      ),
      child: widget.child,
    );
    if (theme != null) {
      return Stack(
        clipBehavior: Clip.none,
        children: [
          RefreshIndicator.noSpinner(
            onRefresh: _refresh,
            onStatusChange: _onStatusChange,
            child: NotificationListener<ScrollNotification>(
              onNotification: _onScrollNotification,
              child: content,
            ),
          ),
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: IgnorePointer(
              child: ValueListenableBuilder<RefreshIndicatorStatus?>(
                valueListenable: _status,
                builder: (context, status, _) =>
                    theme.indicatorBuilder(context, status),
              ),
            ),
          ),
        ],
      );
    }
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      color: context.appColor(AppColors.primary),
      backgroundColor: Colors.white,
      child: content,
    );
  }
}
