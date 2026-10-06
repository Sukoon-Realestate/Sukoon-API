import 'dart:math' as math;
import 'package:flutter/material.dart';

import 'sokoun_motion.dart';

/// A small, settling pulse on a selection change; no entrance or idle motion.
class SokounSelectionFeedback extends StatelessWidget {
  const SokounSelectionFeedback({
    super.key,
    required this.selected,
    required this.child,
  });

  final bool selected;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final duration = SokounMotion.duration(context, milliseconds: 240);
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: selected ? 1 : 0, end: selected ? 1 : 0),
      duration: duration,
      curve: SokounMotion.curve,
      builder: (context, value, child) => Transform.scale(
        scale: duration == Duration.zero
            ? 1
            : 1 + .08 * math.sin(math.pi * value),
        child: child,
      ),
      child: child,
    );
  }
}
