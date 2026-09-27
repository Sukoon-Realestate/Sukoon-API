import 'dart:async';

import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/notification_service.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/widgets/splash_logo.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_coordinator.dart';
import 'main_view/presentation/screens/view.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    unawaited(_manipulateSplashData());
  }

  Future<void> _manipulateSplashData() async {
    await Future.wait<void>([
      Helpers.getCurrentFlavor,
      NotificationService().saveFcmToken(),
      Future<void>.delayed(const Duration(seconds: 2)),
    ]);
    await _manipulateLoginState();
    unawaited(NotificationCoordinator.start());
  }

  Future<void> _manipulateLoginState() async {
    final bool result = await UserCubit.instance.init();
    if (!mounted) return;
    switch (result) {
      case true:
        Go.offAll(const HomeScreen());
        break;

      default:
        Go.offAll(const WelcomeScreen());
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.splash,
      body: SplashLogo(),
    );
  }
}
