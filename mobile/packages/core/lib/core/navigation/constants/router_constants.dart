part of 'imports_constants.dart';

enum PageRouterType {
  material,
  cupertino,
  custom,
}

enum TransitionType {
  slide,
  fade,
  scale,
  rotation,
  size,
  cupertino,
  shake,
}

enum SlideDirection {
  leftToRight,
  rightToLeft,
  topToBottom,
  bottomToTop,
}

class RouterConstants {
  const RouterConstants._();

  static const Duration transitionDuration = Duration(milliseconds: 600);
  static const Duration reverseTransitionDuration = Duration(milliseconds: 300);
  static const Curve transitionCurve = Curves.easeInOut;
  static const Curve reverseTransitionCurve = Curves.easeInOut;

  static const TransitionType defaultTransition = TransitionType.fade;

  static Tween<Offset> leftToRightTween =
      Tween(begin: const Offset(-1, 0), end: const Offset(0, 0));
  static Tween<Offset> rightToLeftTween =
      Tween(begin: const Offset(1, 0), end: const Offset(0, 0));
  static Tween<Offset> topToBottomTween =
      Tween(begin: const Offset(0, -1), end: const Offset(0, 0));
  static Tween<Offset> bottomToTopTween =
      Tween(begin: const Offset(0, 1), end: const Offset(0, 0));
}
