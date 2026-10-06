part of 'helper_imports.dart';

abstract class AnimationOption {
  final Duration? duration;
  final Curve? curve;
  final Curve? reverseCurve;
  final Duration? reverseDuration;
  final bool secondaryTransition;

  const AnimationOption({
    this.duration = const Duration(milliseconds: 300),
    this.curve = Curves.easeInOut,
    this.reverseCurve = Curves.easeInOut,
    this.reverseDuration = const Duration(milliseconds: 300),
    this.secondaryTransition = false,
  });
}
