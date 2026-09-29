import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class SvgPic extends StatelessWidget {
  final String assetName;
  final Color? color;
  final double? size;

  const SvgPic({super.key, required this.assetName, this.color, this.size});

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: size,
      child: SvgPicture.asset(
        package: 'melos_core',
        assetName,
        colorFilter: color == null
            ? null
            : ColorFilter.mode(color!, BlendMode.srcIn),
      ),
    );
  }
}
