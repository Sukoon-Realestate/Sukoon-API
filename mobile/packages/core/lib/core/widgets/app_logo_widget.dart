import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/svg_pic.dart';
import 'package:melos_core/generated/assets.dart';

class AppLogoWidget extends StatelessWidget {
  const AppLogoWidget({super.key, this.size, this.color});

  final double? size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Center(
      widthFactor: 1,
      heightFactor: 1,
      child: SvgPic(
        assetName: Assets.svg.logo.path,
        size: size ?? 100.sp,
        color: color,
      ),
    );
  }
}
