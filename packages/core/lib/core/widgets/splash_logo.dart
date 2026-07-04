import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../generated/assets.dart';
import 'svg_pic.dart';

class SplashLogo extends StatelessWidget {
  const SplashLogo({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(child: SvgPic(assetName: Assets.svgSatr, size: 220.sp));
  }
}