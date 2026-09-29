import 'package:flutter/material.dart';

import 'sokoun_motion.dart';

/// A short, one-time entrance for a coherent section, not every scrolling row.
/// Rebuilds retain both the animation and the child's state.
class SokounReveal extends StatefulWidget {
  const SokounReveal({
    super.key,
    required this.child,
    this.delay = Duration.zero,
  });

  final Widget child;
  final Duration delay;

  @override
  State<SokounReveal> createState() => _SokounRevealState();
}

class _SokounRevealState extends State<SokounReveal>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(vsync: this);
  late Animation<double> _opacity;
  late Animation<Offset> _position;
  bool _started = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final duration = SokounMotion.duration(context, milliseconds: 320);
    if (!_started) {
      _started = true;
      final total = duration + widget.delay;
      _controller.duration = total;
      final curve = CurveTween(
        curve: Interval(
          duration == Duration.zero
              ? 0
              : widget.delay.inMicroseconds / total.inMicroseconds,
          1,
          curve: SokounMotion.curve,
        ),
      ).animate(_controller);
      _opacity = curve;
      _position = Tween(
        begin: const Offset(0, .035),
        end: Offset.zero,
      ).animate(curve);
      if (duration != Duration.zero) _controller.forward();
    }
    if (duration == Duration.zero) _controller.value = 1;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FadeTransition(
    opacity: _opacity,
    child: SlideTransition(position: _position, child: widget.child),
  );
}
