 import 'package:flutter/material.dart';

import '../../../constants/imports_constants.dart';
import '../../Factory/transition_creator.dart';
import 'Option/slide_animation_option.dart';
import 'animator/slide_animator.dart';

class SlideTransitionAnimation implements TransitionCreator {
  final SlideAnimationOptions options;
  const SlideTransitionAnimation({required this.options});
  @override
  Widget animate(
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    return SlideTransition(
      position: SliderAnimator(options).animator(animation),
      child: child,
    ).buildSecondaryTransition(
        animation: animation,
        applySecondaryTransition: options.secondaryTransition);
  }
}
