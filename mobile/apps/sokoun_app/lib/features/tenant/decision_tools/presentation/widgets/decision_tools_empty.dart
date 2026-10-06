import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class DecisionToolsEmpty extends StatelessWidget {
  const DecisionToolsEmpty({
    super.key,
    required this.title,
    required this.description,
  });
  final String title;
  final String description;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(24),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Assets.lottie.emptyBox.lottie(
          package: 'melos_core',
          width: 120,
          height: 110,
          repeat: false,
          animate: !MediaQuery.of(context).disableAnimations,
        ),
        AppText(
          title,
          fontWeight: FontWeight.bold,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        AppText(description, textAlign: TextAlign.center),
      ],
    ),
  );
}
