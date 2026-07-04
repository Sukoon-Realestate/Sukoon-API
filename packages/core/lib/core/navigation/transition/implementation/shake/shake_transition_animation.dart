import 'package:flutter/material.dart';

import '../../Factory/transition_creator.dart';
import 'Options/shake_animation_options.dart';

class ShakeTransitionAnimation implements TransitionCreator {
  final ShakeAnimationOptions options;

  const ShakeTransitionAnimation({required this.options});

  @override
  Widget animate(
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    return TweenAnimationBuilder(
      tween: Tween(begin: 1.0, end: 0.0),
      duration: const Duration(milliseconds: 600),
      curve: Curves.easeInOutBack,
      builder: (_, double value, child) {
        return Transform.translate(
          offset: getOffset(value,
              shakeFactor: -10, direction: ShakeDirection.horizontal),
          child: child,
        );
      },
      child: child,
    );
  }
}

enum ShakeDirection { horizontal, vertical }

Offset getOffset(
  double value, {
  ShakeDirection direction = ShakeDirection.horizontal,
  double shakeFactor = 1,
}) {
  switch (direction) {
    case ShakeDirection.horizontal:
      return Offset(value * shakeFactor, 0);
    case ShakeDirection.vertical:
      return Offset(0, value * shakeFactor);
  }
}
