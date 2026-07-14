import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

class TenantNearbyPlaceRow extends StatelessWidget {
  const TenantNearbyPlaceRow({super.key, required this.place});

  final TenantNearbyPlaceContent place;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8.h),
      child: Row(
        children: [
          Container(
            width: 34.r,
            height: 34.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.mintLight,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(place.icon, color: AppColors.sokoonTeal, size: 17.r),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  place.title,
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w900,
                ),
                3.szH,
                AppText(
                  place.subtitle,
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w500,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
