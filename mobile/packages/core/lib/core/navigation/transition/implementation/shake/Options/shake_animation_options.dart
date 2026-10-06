import '../../../../Helper/Interfaces/helper_imports.dart';

class ShakeAnimationOptions extends AnimationOption {
  final double begin;
  final double end;
  final double shakeAngle;
  final double shakeOffset;
  final int factor;

  const ShakeAnimationOptions({
    this.begin = 0.0,
    this.end = 1.0,
    this.shakeAngle = 0.0,
    this.shakeOffset = 0.0,
    this.factor = 1,
    super.duration,
    super.curve,
    super.reverseCurve,
    super.reverseDuration,
    super.secondaryTransition,
  });
}
