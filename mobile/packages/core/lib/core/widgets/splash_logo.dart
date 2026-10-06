import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import 'app_logo_widget.dart';

class SplashLogo extends StatelessWidget {
  const SplashLogo({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: AppLogoWidget(size: 120.r, color: Colors.white),
    );
  }
}
