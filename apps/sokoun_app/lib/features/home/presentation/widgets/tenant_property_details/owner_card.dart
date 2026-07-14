import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

class TenantPropertyOwnerCard extends StatelessWidget {
  const TenantPropertyOwnerCard({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 44.r,
                height: 44.r,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.tealAlpha13,
                  borderRadius: BorderRadius.circular(22.r),
                ),
                child: Icon(
                  Icons.person_outline_rounded,
                  color: AppColors.sokoonTeal,
                  size: 22.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: AppText(
                            property.ownerName,
                            color: AppColors.sokoonNavy,
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w900,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        6.szW,
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 6.w,
                            vertical: 2.h,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.sokoonTeal,
                            borderRadius: BorderRadius.circular(6.r),
                          ),
                          child: AppText(
                            'موثّق',
                            color: AppColors.white,
                            fontSize: 10.sp,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ],
                    ),
                    4.szH,
                    AppText(
                      property.ownerMeta,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w500,
                    ),
                  ],
                ),
              ),
            ],
          ),
          12.szH,
          Container(
            padding: EdgeInsets.all(10.w),
            decoration: BoxDecoration(
              color: AppColors.grayOffWhite,
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.lock_outline_rounded,
                  color: AppColors.sokoonGray,
                  size: 16.r,
                ),
                8.szW,
                Expanded(
                  child: AppText(
                    'رقم الموبايل مخفي ومش هيظهر غير بموافقة واضحة',
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
