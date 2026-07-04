import 'package:flutter/material.dart';

import '../../config/language/locale_keys.g.dart';
import '../../config/res/assets.gen.dart';
import '../../config/res/config_imports.dart';
import '../extensions/context_extension.dart';
import '../extensions/text_style_extensions.dart';

class InternetExpetion extends StatelessWidget {
  const InternetExpetion({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        spacing: AppMargin.mH10,
        children: [
          AppAssets.lottie.network.noInternet.lottie(
            width: context.width * .7,
            height: context.height * .3,
          ),
          Text(
            LocaleKeys.errorExeptionNointernetDesc,
            style: const TextStyle().setPrimaryColor.s13.medium,
          ),
        ],
      ),
    );
  }
}
