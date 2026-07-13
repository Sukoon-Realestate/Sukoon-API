import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_request_content.dart';

class OwnerRequestStatusChip extends StatelessWidget {
  const OwnerRequestStatusChip({super.key, required this.status});

  final OwnerRequestStatusContent status;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 5.h),
      decoration: BoxDecoration(
        color: status.backgroundColor,
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: AppText(
        status.label,
        color: status.foregroundColor,
        fontSize: 12.sp,
        fontWeight: FontWeight.w900,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }
}
