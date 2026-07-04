import 'package:flutter/material.dart';

import '../../config/language/locale_keys.g.dart';
import '../../config/res/assets.gen.dart';
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
            AppAssets.lottie.error.error1.lottie(),
            AppText(LocaleKeys.checkInternet),
          ],
        ),
      ),
    );
  }
}
