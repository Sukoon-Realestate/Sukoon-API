import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:sokoun_app/features/shared/appearance/presentation/cubits/theme_cubit.dart';

import 'sokoun_motion.dart';
import 'sokoun_theme.dart';
import 'sokoun_theme_config.dart';

/// Keeps theme changes above the navigator so routes and form state survive.
class SokounThemedApp extends StatelessWidget {
  const SokounThemedApp({super.key, required this.home});

  final Widget home;

  @override
  Widget build(BuildContext context) => BlocBuilder<ThemeCubit, ThemeMode>(
    builder: (context, mode) => MaterialApp(
      debugShowCheckedModeBanner: false,
      title: ConstantManager.projectName,
      theme: SokounTheme.light,
      darkTheme: SokounTheme.dark,
      themeMode: mode,
      themeAnimationDuration: SokounMotion.duration(
        context,
        milliseconds: SokounThemeConfig.transitionMilliseconds,
      ),
      themeAnimationCurve: SokounThemeConfig.transitionCurve,
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      navigatorKey: Go.navigatorKey,
      initialRoute: '/',
      home: home,
      builder: (context, child) {
        final ThemeData theme = Theme.of(context);
        final bool dark = theme.brightness == Brightness.dark;
        return AnnotatedRegion<SystemUiOverlayStyle>(
          value: SystemUiOverlayStyle(
            statusBarColor: AppColors.transparent,
            statusBarIconBrightness: dark ? Brightness.light : Brightness.dark,
            statusBarBrightness: dark ? Brightness.dark : Brightness.light,
            systemNavigationBarColor: theme.scaffoldBackgroundColor,
            systemNavigationBarIconBrightness: dark
                ? Brightness.light
                : Brightness.dark,
          ),
          child: child!,
        );
      },
      navigatorObservers: [AppNavigationObserver.instance],
    ),
  );
}
