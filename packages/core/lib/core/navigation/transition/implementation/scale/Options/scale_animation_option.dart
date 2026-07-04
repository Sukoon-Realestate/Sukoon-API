import '../../../../Helper/Interfaces/helper_imports.dart';

class ScaleAnimationOptions extends AnimationOption {
  final double begin;
  final double end;
  const ScaleAnimationOptions({
    this.begin = 0.0,
    this.end = 1.0,
    super.duration,
    super.curve,
    super.reverseCurve,
    super.reverseDuration,
    super.secondaryTransition,
  });
}
