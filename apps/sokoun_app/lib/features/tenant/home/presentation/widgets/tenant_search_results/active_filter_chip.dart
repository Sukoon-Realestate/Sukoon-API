import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';

class ActiveFilterChip extends StatelessWidget {
  const ActiveFilterChip({super.key, required this.filter, this.onRemove});

  final ActiveFilterContent filter;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 30.h,
      padding: EdgeInsetsDirectional.only(start: 10.w, end: 8.w),
      decoration: BoxDecoration(
        color: AppColors.tealAlpha07,
        borderRadius: BorderRadius.circular(999.r),
        border: Border.all(color: AppColors.tealAlpha19),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          AppText(
            filter.label,
            color: AppColors.sokoonTeal,
            fontSize: 12.sp,
            fontWeight: FontWeight.w600,
          ),
          5.szW,
          GestureDetector(
            onTap: onRemove,
            behavior: HitTestBehavior.opaque,
            child: Icon(
              Icons.close_rounded,
              color: AppColors.sokoonTeal,
              size: 14.r,
            ),
          ),
        ],
      ),
    );
  }
}
