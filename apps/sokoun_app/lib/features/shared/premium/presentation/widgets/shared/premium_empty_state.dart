import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

class PremiumEmptyState extends StatelessWidget {
  const PremiumEmptyState({
    super.key,
    required this.title,
    required this.description,
  });
  final String title;
  final String description;
  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.all(24.r),
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ExcludeSemantics(
          child: Assets.lottie.emptyBox.lottie(
            package: 'melos_core',
            height: 110.r,
            width: 120.r,
            animate: !MediaQuery.of(context).disableAnimations,
            repeat: false,
          ),
        ),
        AppText(
          title,
          fontWeight: FontWeight.bold,
          textAlign: TextAlign.center,
        ),
        8.szH,
        AppText(description, textAlign: TextAlign.center),
      ],
    ),
  );
}
