import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantPropertyCard extends StatelessWidget {
  const TenantPropertyCard({
    super.key,
    required this.title,
    required this.rating,
    required this.area,
    required this.price,
    required this.icon,
  });

  final String title;
  final String rating;
  final String area;
  final String price;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 94.h,
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      clipBehavior: Clip.antiAlias,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Container(
            width: 96.w,
            height: double.infinity,
            color: AppColors.grayBluePale,
            child: Icon(icon, color: AppColors.blueGrayLight, size: 26.r),
          ),
          Expanded(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  AppText(
                    title,
                    color: AppColors.sokoonNavy,
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w900,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  6.szH,
                  Row(
                    children: [
                      Icon(
                        Icons.star_rounded,
                        color: AppColors.amber,
                        size: 14.r,
                      ),
                      3.szW,
                      AppText(
                        rating,
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                      8.szW,
                      AppText(
                        '·',
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                      8.szW,
                      AppText(
                        area,
                        color: AppColors.sokoonGray,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                    ],
                  ),
                  const Spacer(),
                  Align(
                    alignment: AlignmentDirectional.centerEnd,
                    child: AppText(
                      price,
                      color: AppColors.sokoonTeal,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
