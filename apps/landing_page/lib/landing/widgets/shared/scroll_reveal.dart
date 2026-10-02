import 'package:flutter/material.dart';

/// One-shot entrance, started only when the content reaches the viewport.
/// No timers or repeating tickers remain active after the entrance finishes.
class ScrollReveal extends StatefulWidget {
  const ScrollReveal({required this.child, this.delay = 0, super.key});

  final Widget child;
  final int delay;

  @override
  State<ScrollReveal> createState() => _ScrollRevealState();
}

class _ScrollRevealState extends State<ScrollReveal>
    with SingleTickerProviderStateMixin {
  late final _controller = AnimationController(
    vsync: this,
    duration: Duration(milliseconds: 650 + widget.delay),
  );
  late final CurvedAnimation _progress = CurvedAnimation(
    parent: _controller,
    curve: Interval(
      widget.delay / (650 + widget.delay),
      1,
      curve: Curves.easeOutCubic,
    ),
  );
  ScrollPosition? _position;
  bool _scheduled = false;
  bool _revealed = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final position = Scrollable.maybeOf(context)?.position;
    if (position != _position) {
      _position?.removeListener(_scheduleCheck);
      _position = position;
      if (!_revealed) _position?.addListener(_scheduleCheck);
    }
    if (MediaQuery.disableAnimationsOf(context) ||
        MediaQuery.accessibleNavigationOf(context)) {
      _revealed = true;
      _controller.value = 1;
      _position?.removeListener(_scheduleCheck);
    } else {
      _scheduleCheck();
    }
  }

  void _scheduleCheck() {
    if (_scheduled || _revealed) return;
    _scheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scheduled = false;
      if (!mounted || _revealed) return;
      final box = context.findRenderObject();
      if (box is! RenderBox || !box.hasSize) return;
      final top = box.localToGlobal(Offset.zero).dy;
      if (top < MediaQuery.sizeOf(context).height * .96 &&
          top + box.size.height > 0) {
        _revealed = true;
        _position?.removeListener(_scheduleCheck);
        _controller.forward();
      }
    });
  }

  @override
  void dispose() {
    _position?.removeListener(_scheduleCheck);
    _progress.dispose();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FadeTransition(
    opacity: _progress,
    alwaysIncludeSemantics: true,
    child: AnimatedBuilder(
      animation: _progress,
      child: widget.child,
      builder: (context, child) => Transform.translate(
        offset: Offset(0, 24 * (1 - _progress.value)),
        child: child,
      ),
    ),
  );
}
