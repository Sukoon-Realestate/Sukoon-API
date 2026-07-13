import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class HomeSectionHeader extends StatelessWidget {
  const HomeSectionHeader({
    super.key,
    required this.title,
    this.actionTitle,
    this.onActionTap,
  });

  final String title;
  final String? actionTitle;
  final VoidCallback? onActionTap;

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      children: [
        if (actionTitle != null)
          TextButton(
            onPressed: onActionTap,
            style: TextButton.styleFrom(
              minimumSize: Size.zero,
              padding: EdgeInsets.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: AppText(
              actionTitle!,
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
            ),
          ),
        const Spacer(),
        AppText(
          title,
          color: AppColors.sokoonNavy,
          fontSize: 15.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.right,
        ),
      ],
    );
  }
}
