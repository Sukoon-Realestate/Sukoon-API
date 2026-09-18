import 'dart:async';

import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/notification_service.dart';
import 'package:melos_core/core/widgets/splash_logo.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/role_select_screen.dart';

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
    Go.offAll(RoleSelectScreen());
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.splash,
      body: SplashLogo(),
    );
  }
}
