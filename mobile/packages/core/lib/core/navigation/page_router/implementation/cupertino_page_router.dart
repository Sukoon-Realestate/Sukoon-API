part of 'imports_page_router.dart';

class CupertinoPageRouterCreator implements PageRouterCreator {
  @override
  Route<T> create<T>(
    Widget page, {
    RouteSettings? settings,
    TransitionType? transition,
    AnimationOption? animationOptions,
  }) {
    return CupertinoPageRoute(
      builder: (context) => page,
      settings: settings,
    );
  }
}
