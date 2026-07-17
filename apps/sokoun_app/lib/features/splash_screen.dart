import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/object.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/notification_service.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/widgets/splash_logo.dart';
import 'package:sokoun_app/features/auth/presentation/screens/role_select_screen.dart';

import 'auth/presentation/screens/login_screen.dart';
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

  void _manipulateSplashData()async{
    await Helpers.getCurrentFlavor;
    await NotificationService().saveFcmToken();
    await Future.delayed(const Duration(seconds: 2));
    _manipulateLoginState();
  }

  Future<void> _manipulateLoginState()async{
    final result =  (await CacheStorage.read('user', isDecoded: true) as Object?).isNotNull;
    switch(result){
      case true:
        await UserCubit.instance.init();
        Go.offAll(const HomeScreen());
        break;

      default:
        Go.offAll(RoleSelectScreen());
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
        backgroundColor: AppColors.splash,
        body: SplashLogo()
    );
  }
}
