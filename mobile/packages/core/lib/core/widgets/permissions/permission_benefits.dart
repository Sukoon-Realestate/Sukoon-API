import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import 'permission_benefit_row.dart';

class PermissionBenefits extends StatelessWidget {
  const PermissionBenefits({
    super.key,
    required this.backgroundColor,
    required this.children,
  });

  final Color backgroundColor;
  final List<PermissionBenefitRow> children;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        spacing: 10.h,
        children: children,
      ),
    );
  }
}
