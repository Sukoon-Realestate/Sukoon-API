import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantPropertyAmenityWrap extends StatelessWidget {
  const TenantPropertyAmenityWrap({super.key, required this.amenities});

  final List<String> amenities;

  @override
  Widget build(BuildContext context) {
    final uniqueAmenities = amenities.toSet().toList();
    return Wrap(
      alignment: WrapAlignment.end,
      spacing: 8.w,
      runSpacing: 8.h,
      children: [
        for (final amenity in uniqueAmenities)
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
            decoration: BoxDecoration(
              color: AppColors.tealAlpha07,
              borderRadius: BorderRadius.circular(999.r),
            ),
            child: AppText(
              amenity,
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
            ),
          ),
      ],
    );
  }
}
