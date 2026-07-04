part of 'imports_constants.dart';

extension AnimationExtension on AnimatedWidget {
  Widget buildSecondaryTransition({
    required Animation<double> animation,
    required bool applySecondaryTransition,
  }) {
    if (applySecondaryTransition) {
      return FadeTransition(
        opacity: FadeAnimator(const FadeAnimationOptions()).animator(animation),
        child: this,
      );
    } else {
      return this;
    }
  }
}
