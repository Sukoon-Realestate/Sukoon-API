import '../../../../Helper/Interfaces/helper_imports.dart';

class CupertinoAnimationOptions extends AnimationOption {
  final bool isFullscreenDialog;
  final bool isLinearTransition;
  const CupertinoAnimationOptions({
    this.isFullscreenDialog = false,
    this.isLinearTransition = false,
    super.duration,
    super.curve,
    super.reverseCurve,
    super.reverseDuration,
  });
}
