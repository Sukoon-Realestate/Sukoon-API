import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerVisitRequestTimeRow extends StatelessWidget {
  const OwnerVisitRequestTimeRow({super.key, required this.dateLabel});

  final String dateLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: AppColors.grayOffWhite,
        borderRadius: BorderRadius.circular(10.r),
      ),
      child: Row(
        textDirection: TextDirection.rtl,
        children: [
          Icon(
            Icons.calendar_today_outlined,
            color: AppColors.sokoonGray,
            size: 14.r,
          ),
          6.szW,
          Expanded(
            child: AppText(
              dateLabel,
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              fontWeight: FontWeight.w400,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
