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
        ? AppColors.sokoonTeal
        : AppColors.sokoonMuted;

    return Container(
      padding: EdgeInsets.all(14.r),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(
          color: isHighlighted ? AppColors.tealAlpha19 : AppColors.grayPale,
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
                  : AppColors.grayBackground,
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Icon(icon, color: accentColor, size: 18.r),
          ),
          12.szW,
          Expanded(
            child: AppText(
              title,
              style: AppTextStyles.semiBold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (isComplete)
            Icon(Icons.check_rounded, color: AppColors.sokoonTeal, size: 18.r),
        ],
      ),
    );
  }
}
