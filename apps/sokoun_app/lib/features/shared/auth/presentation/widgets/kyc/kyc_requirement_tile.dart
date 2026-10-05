import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class KycRequirementTile extends StatelessWidget {
  const KycRequirementTile({
    super.key,
    required this.icon,
    required this.title,
    this.isHighlighted = false,
    this.isComplete = false,
  });

  final IconData icon;
  final String title;
  final bool isHighlighted;
  final bool isComplete;

  @override
  Widget build(BuildContext context) {
    final accentColor = isHighlighted
        ? context.appColor(AppColors.sokoonTeal)
        : context.appColor(AppColors.sokoonMuted);

    return Container(
      padding: EdgeInsets.all(14.r),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(
          color: isHighlighted
              ? AppColors.tealAlpha19
              : context.appColor(AppColors.grayPale),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            decoration: BoxDecoration(
              color: isHighlighted
                  ? AppColors.tealAlpha09
                  : context.appColor(AppColors.grayBackground, surface: true),
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Icon(icon, color: context.appColor(accentColor), size: 18.r),
          ),
          12.szW,
          Expanded(
            child: AppText(
              title,
              style: AppTextStyles.semiBold.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 14.sp,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (isComplete)
            Icon(
              Icons.check_rounded,
              color: context.appColor(AppColors.sokoonTeal),
              size: 18.r,
            ),
        ],
      ),
    );
  }
}
