import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';

import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import 'app_text.dart';

class NoInternetWidget extends StatelessWidget {
  const NoInternetWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          spacing: AppMargin.mH10,
          children: [
            Lottie.asset('assets/lottie/error_1.json', package: 'melos_core'),
            AppText(LocaleKeys.checkInternet),
          ],
        ),
      ),
    );
  }
}
