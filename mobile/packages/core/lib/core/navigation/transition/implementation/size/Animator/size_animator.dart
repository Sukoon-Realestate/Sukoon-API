import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';

import '../../../../Constants/imports_constants.dart';
import '../../../../Helper/Interfaces/helper_imports.dart';
import '../Option/size_animation_option.dart';

class SizeAnimator extends Animator<double>
    implements CurveBehaviour, TweenBehaviour<double> {
  final SizeAnimationOptions options;

  SizeAnimator(this.options);

  @override
  CurvedAnimation setCurveAnimation(Animation<double> animation) {
    return CurvedAnimation(
      parent: animation,
      curve: options.curve ?? RouterConstants.transitionCurve,
      reverseCurve:
          options.reverseCurve ?? RouterConstants.reverseTransitionCurve,
    );
  }

  @override
  Tween<double> setTween() {
    return Tween<double>(
      begin: options.begin,
      end: options.end,
    );
  }

  @override
  Animation<double> animator(Animation<double> animation) {
    return setTween().animate(setCurveAnimation(animation));
  }
}
