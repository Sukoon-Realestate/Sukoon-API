import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

class SuggestedAreaCard extends StatelessWidget {
  const SuggestedAreaCard({
    super.key,
    required this.area,
    this.isSelected = false,
    this.onTap,
  });

  final SuggestedAreaContent area;
  final bool isSelected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 86.h,
        padding: EdgeInsets.all(12.w),
        decoration: BoxDecoration(
          color: area.backgroundColor,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(
            color: isSelected ? AppColors.sokoonTeal : AppColors.transparent,
            width: 1.4,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(area.icon, color: area.iconColor, size: 18.r),
            7.szH,
            AppText(
              area.title,
              color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonNavy,
              fontSize: 12.sp,
              fontWeight: FontWeight.w900,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.right,
            ),
            3.szH,
            AppText(
              area.subtitle,
              color: AppColors.sokoonGray,
              fontSize: 10.sp,
              fontWeight: FontWeight.w600,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.right,
            ),
          ],
        ),
      ),
    );
  }
}
