part of 'imports_page_router.dart';

class CustomPageRouterCreator implements PageRouterCreator {
  final TransitionType? parentTransition;
  final AnimationOption? parentOptions;

  CustomPageRouterCreator({
    this.parentTransition,
    this.parentOptions,
  });
  @override
  Route<T> create<T>(
    Widget page, {
    RouteSettings? settings,
    TransitionType? transition,
    AnimationOption? animationOptions,
  }) {
    final transitionType =
        transition ?? parentTransition ?? RouterConstants.defaultTransition;
    final options = animationOptions ??
        (transitionType == parentTransition ? parentOptions : null);
    // animationOptions ?? parentOptions;

    return PageRouteBuilder(
      pageBuilder: (context, animation, secondaryAnimation) => page,
      settings: settings,
      maintainState: true,
      transitionDuration:
          options?.duration ?? RouterConstants.transitionDuration,
      reverseTransitionDuration:
          options?.reverseDuration ?? RouterConstants.reverseTransitionDuration,
      transitionsBuilder: (BuildContext context, Animation<double> animation,
          Animation<double> secondaryAnimation, Widget child) {
        return TransitionTypeBuilder.create(
          type: transitionType,
          options: options,
        ).animate(
          animation,
          secondaryAnimation,
          child,
        );
      },
    );
  }
}
