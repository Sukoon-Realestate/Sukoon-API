part of 'imports_transition_builder.dart';

class TransitionTypeBuilder {
  static TransitionCreator create({
    required TransitionType type,
    AnimationOption? options,
  }) {
    switch (type) {
      case TransitionType.slide:
        final slideOptions = options as SlideAnimationOptions?;
        return SlideTransitionAnimation(
            options: slideOptions ?? const SlideAnimationOptions());
      case TransitionType.fade:
        final fadeOptions = options as FadeAnimationOptions?;
        return FadeTransitionAnimation(
            options: fadeOptions ?? const FadeAnimationOptions());
      case TransitionType.scale:
        final scaleOptions = options as ScaleAnimationOptions?;
        return ScaleTransitionAnimation(
            options: scaleOptions ?? const ScaleAnimationOptions());
      case TransitionType.rotation:
        final rotationOptions = options as RotationAnimationOptions?;
        return RotationTransitionAnimation(
            options: rotationOptions ?? const RotationAnimationOptions());
      case TransitionType.cupertino:
        final cupertinoOptions = options as CupertinoAnimationOptions?;
        return CupertinoTransitionAnimation(
            options: cupertinoOptions ?? const CupertinoAnimationOptions());
      case TransitionType.size:
        final sizeOptions = options as SizeAnimationOptions?;
        return SizeTransitionAnimation(
            options: sizeOptions ?? const SizeAnimationOptions());
      case TransitionType.shake:
        final shakeOptions = options as ShakeAnimationOptions?;
        return ShakeTransitionAnimation(
            options: shakeOptions ?? const ShakeAnimationOptions());
    }
  }
}
