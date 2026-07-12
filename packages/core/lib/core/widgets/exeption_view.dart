import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';
import '../../../generated/assets.dart';

class ExceptionView extends StatelessWidget {
  final Size? size;
  const ExceptionView({super.key, this.size});

  @override
  Widget build(BuildContext context) {
    return FittedBox(
      child: Lottie.asset(
        Assets.lottie.error1.path,
        width: size?.width,
        height: size?.height,
        fit: BoxFit.contain,
      ),
    );
  }
}
