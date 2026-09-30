import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/Constants/imports_constants.dart';
import 'package:melos_core/core/navigation/Transition/implementation/fade/Option/fade_animation_option.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/notification_service.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_coordinator.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';

import 'main_view/presentation/screens/view.dart';
import 'splash/presentation/widgets/animated_splash_logo.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final Completer<void> _logoAnimationCompleted = Completer<void>();

  @override
  void initState() {
    super.initState();
    unawaited(_manipulateSplashData());
  }

  Future<void> _manipulateSplashData() async {
    await Future.wait<void>([
      Helpers.getCurrentFlavor,
      NotificationService().saveFcmToken(),
      _logoAnimationCompleted.future,
    ]);
    if (!mounted) return;
    await _manipulateLoginState();
  }

  void _onLogoAnimationCompleted() {
    if (!_logoAnimationCompleted.isCompleted) {
      _logoAnimationCompleted.complete();
    }
  }

  @override
  void dispose() {
    // Release the startup wait if another route removes the splash early.
    _onLogoAnimationCompleted();
    super.dispose();
  }

  Future<void> _manipulateLoginState() async {
    final bool result = await UserCubit.instance.init();
    if (!mounted) return;
    Go.offAll(
      result ? const HomeScreen() : const WelcomeScreen(),
      transition: TransitionType.fade,
      options: FadeAnimationOptions(
        duration: SokounMotion.duration(context, milliseconds: 400),
        curve: Curves.easeInOutCubic,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.dark.copyWith(
        statusBarColor: AppColors.transparent,
        systemNavigationBarColor: AppColors.sokoonSplashBackground,
        systemNavigationBarDividerColor: AppColors.sokoonSplashBackground,
      ),
      child: Scaffold(
        backgroundColor: AppColors.sokoonSplashBackground,
        body: AnimatedSplashLogo(onCompleted: _onLogoAnimationCompleted),
      ),
    );
  }
}
