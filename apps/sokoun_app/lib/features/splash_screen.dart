import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/splash_logo.dart';
import 'main_view/presentation/screens/view.dart';

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
    await Future.delayed(const Duration(seconds: 2));
    Go.offAll(const HomeScreen());
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.splash,
      body: SplashLogo(),
    );
  }
}
