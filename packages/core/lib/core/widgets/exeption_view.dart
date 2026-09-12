import 'package:flutter/material.dart';
import '../../../generated/assets.dart';

class ExceptionView extends StatelessWidget {
  final Size? size;
  const ExceptionView({super.key, this.size});

  @override
  Widget build(BuildContext context) {
    return FittedBox(
      child: Assets.lottie.error2.lottie(
        package: 'melos_core',
        width: size?.width,
        height: size?.height,
        fit: BoxFit.contain,
      ),
    );
  }
}
