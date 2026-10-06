part of 'imports_page_router_builder.dart';

class PageRouterBuilder {
  PageRouterBuilder._();

  factory PageRouterBuilder() => _instance;
  static final PageRouterBuilder _instance = PageRouterBuilder._();

  PageRouterCreator _creator = CustomPageRouterCreator();

  void initAppRouter({
    PlatformConfig? config,
  }) {
    final platform = Platform.operatingSystem;
    switch (platform) {
      case 'android':
        _creator = config?.android ?? MaterialPageRouterCreator();
        break;
      case 'ios':
        _creator = config?.ios ?? CupertinoPageRouterCreator();
        break;
      case 'windows':
        _creator = config?.web ??
            CustomPageRouterCreator(parentTransition: TransitionType.fade);
        break;
      default:
        _creator = CupertinoPageRouterCreator();
    }
  }

  Route<T> build<T>(
    Widget page, {
    RouteSettings? settings,
    TransitionType? transition,
    AnimationOption? options,
  }) {
    return _creator.create<T>(
      page,
      settings: settings,
      transition: transition,
      animationOptions: options,
    );
  }
}

class PlatformConfig {
  final PageRouterCreator? android;
  final PageRouterCreator? ios;
  final PageRouterCreator? web;
  PlatformConfig({
    this.android,
    this.ios,
    this.web,
  });
}
