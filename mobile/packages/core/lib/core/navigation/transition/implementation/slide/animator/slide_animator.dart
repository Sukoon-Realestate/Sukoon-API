import 'package:flutter/animation.dart';

import '../../../../Constants/imports_constants.dart';
import '../../../../Helper/Interfaces/helper_imports.dart';
import '../Option/slide_animation_option.dart';

class SliderAnimator extends Animator<Offset>
    implements TweenBehaviour<Offset>, CurveBehaviour {
  final SlideAnimationOptions options;
  SliderAnimator(this.options);

  final Map<SlideDirection, Tween<Offset>> _tweenMap = {
    SlideDirection.leftToRight: RouterConstants.leftToRightTween,
    SlideDirection.rightToLeft: RouterConstants.rightToLeftTween,
    SlideDirection.topToBottom: RouterConstants.topToBottomTween,
    SlideDirection.bottomToTop: RouterConstants.bottomToTopTween,
  };

  @override
  Tween<Offset> setTween() {
    return options.customTween ??
        _tweenMap[options.direction ?? SlideDirection.leftToRight] ??
        RouterConstants.leftToRightTween;
  }

  @override
  CurvedAnimation setCurveAnimation(
    Animation<double> animation,
  ) {
    return CurvedAnimation(
      parent: animation,
      curve: options.curve ?? RouterConstants.transitionCurve,
      reverseCurve:
          options.reverseCurve ?? RouterConstants.reverseTransitionCurve,
    );
  }

  @override
  Animation<Offset> animator(Animation<double> animation) =>
      setTween().animate(setCurveAnimation(animation));
}
