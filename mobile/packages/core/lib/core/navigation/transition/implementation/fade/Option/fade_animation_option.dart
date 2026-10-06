import '../../../../Helper/Interfaces/helper_imports.dart';

class FadeAnimationOptions extends AnimationOption {
  final double begin;
  final double end;
  const FadeAnimationOptions({
    this.begin = 0.0,
    this.end = 1.0,
    super.duration,
    super.curve,
    super.reverseCurve,
    super.reverseDuration,
  });
}
