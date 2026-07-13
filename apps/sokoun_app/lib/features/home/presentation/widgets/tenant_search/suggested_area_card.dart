import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

class SuggestedAreaCard extends StatelessWidget {
  const SuggestedAreaCard({super.key, required this.area});

  final SuggestedAreaContent area;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 86.h,
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: area.backgroundColor,
        borderRadius: BorderRadius.circular(16.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(area.icon, color: area.iconColor, size: 18.r),
          7.szH,
          AppText(
            area.title,
            color: AppColors.sokoonNavy,
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
    );
  }
}
