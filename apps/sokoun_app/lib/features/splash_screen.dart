import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/notification_service.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/widgets/splash_logo.dart';
import 'package:sokoun_app/features/auth/presentation/screens/role_select_screen.dart';

import 'home/presentation/screens/home_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    _manipulateSplashData();
    super.initState();
  }

  Future<void> _manipulateSplashData() async {
    await Helpers.getCurrentFlavor;
    await NotificationService().saveFcmToken();
    await Future.delayed(const Duration(seconds: 2));
    Go.offAll(const HomeScreen());
    // await _manipulateLoginState();
  }

  Future<void> _manipulateLoginState() async {
    final bool isLoggedIn = await UserCubit.instance.init();
    if (isLoggedIn) {
      Go.offAll(const HomeScreen());
      return;
    }

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
