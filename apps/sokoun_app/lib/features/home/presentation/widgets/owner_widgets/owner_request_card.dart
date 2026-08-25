import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class OwnerRequestCard extends StatelessWidget {
  const OwnerRequestCard({
    super.key,
    required this.name,
    required this.details,
    this.avatarUrl,
  });

  final String name;
  final String details;
  final String? avatarUrl;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(color: AppColors.sokoonBorder),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowBlack04,
            blurRadius: 4,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Container(
            width: 38.r,
            height: 38.r,
            decoration: const BoxDecoration(
              color: AppColors.bluePale,
              shape: BoxShape.circle,
            ),
            child: avatarUrl?.isNotEmpty ?? false
                ? ClipOval(
                    child: Image.network(
                      avatarUrl!,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) => Icon(
                        Icons.person_outline,
                        color: AppColors.blue,
                        size: 20.r,
                      ),
                    ),
                  )
                : Icon(Icons.person_outline, color: AppColors.blue, size: 20.r),
          ),
          10.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  name,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  details,
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w400,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          8.szW,
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              DefaultButton(
                onTap: () {},
                title: 'قبول',
                color: AppColors.emerald,
                textColor: AppColors.white,
                borderRadius: BorderRadius.circular(10.r),
                width: 45.w,
                height: 30.h,
                fontSize: 12.sp,
                fontWeight: FontWeight.w900,
              ),
              5.szW,
              DefaultButton(
                onTap: () {},
                title: 'رفض',
                color: AppColors.redPale,
                textColor: AppColors.red,
                borderRadius: BorderRadius.circular(10.r),
                width: 43.w,
                height: 30.h,
                fontSize: 12.sp,
                fontWeight: FontWeight.w900,
              ),
            ],
          ),
        ],
      ),
    );
  }
}
