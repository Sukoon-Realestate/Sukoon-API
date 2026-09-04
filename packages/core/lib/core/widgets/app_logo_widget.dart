import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/svg_pic.dart';

class AppLogoWidget extends StatelessWidget {
  const AppLogoWidget({super.key, this.size, this.color});

  static const String _logoAsset =
      'packages/melos_core/assets/svg/building.svg';

  final double? size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return SvgPic(assetName: _logoAsset, size: size, color: color);
  }
}
