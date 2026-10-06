// import 'package:flutter/material.dart';
//
// import '../../features/splash/splash_screen.dart';
// import 'named_routes.dart';
// import 'page_router/imports_page_router_builder.dart';
//
// class RouterGenerator {
//   RouterGenerator._();
//
//   static final PageRouterBuilder _pageRouter = PageRouterBuilder();
//
//   static Route<dynamic> getRoute(RouteSettings settings) {
//     final namedRoute =
//         NamedRoutes.values.firstWhere((e) => e.routeName == settings.name);
//     return switch (namedRoute) {
//       NamedRoutes.splash => _pageRouter.build(
//           const SplashScreen(),
//           settings: settings,
//         ),
//     };
//   }
//
//   static Route<dynamic> undefineRoute() {
//     return MaterialPageRoute(
//       builder: (_) => const Scaffold(
//         body: Center(
//           child: Text('No route exists here ! '),
//         ),
//       ),
//     );
//   }
// }
