import 'package:flutter/material.dart';

import 'sokoun_motion.dart';

/// Animates a change of context while retaining the child's element and state.
/// Unlike a switcher, this never keeps a second, interactive copy of the page.
class SokounContentTransition extends StatefulWidget {
  const SokounContentTransition({
    super.key,
    required this.identity,
    required this.child,
  });

  final Object? identity;
  final Widget child;

  @override
  State<SokounContentTransition> createState() =>
      _SokounContentTransitionState();
}

class _SokounContentTransitionState extends State<SokounContentTransition>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    value: 1,
  );
  late final Animation<double> _progress = _controller.drive(
    CurveTween(curve: SokounMotion.curve),
  );
  late final Animation<double> _opacity = _progress.drive(
    Tween(begin: .65, end: 1),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _controller.duration = SokounMotion.duration(context, milliseconds: 240);
    if (_controller.duration == Duration.zero || !TickerMode.of(context)) {
      _controller.value = 1;
    }
  }

  @override
  void didUpdateWidget(covariant SokounContentTransition oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.identity != oldWidget.identity &&
        SokounMotion.duration(context) != Duration.zero &&
        TickerMode.of(context)) {
      _controller.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FadeTransition(
    opacity: _opacity,
    child: AnimatedBuilder(
      animation: _progress,
      builder: (context, child) => Transform.translate(
        offset: Offset(0, 8 * (1 - _progress.value)),
        child: child,
      ),
      child: widget.child,
    ),
  );
}
