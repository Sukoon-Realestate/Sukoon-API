import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

class TenantPropertyTagRow extends StatelessWidget {
  const TenantPropertyTagRow({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 7.w,
      runSpacing: 7.h,
      alignment: WrapAlignment.end,
      children: [
        _SmallTag(
          label: property.propertyType,
          backgroundColor: AppColors.tealAlpha09,
          textColor: AppColors.sokoonTeal,
        ),
        if (property.isFurnished)
          const _SmallTag(
            label: 'مفروشة',
            backgroundColor: AppColors.grayBackground,
            textColor: AppColors.sokoonGray,
          ),
        if (property.isVerified)
          const _SmallTag(
            label: 'موثّق ✓',
            backgroundColor: AppColors.greenAlpha09,
            textColor: AppColors.green,
          ),
      ],
    );
  }
}

class _SmallTag extends StatelessWidget {
  const _SmallTag({
    required this.label,
    required this.backgroundColor,
    required this.textColor,
  });

  final String label;
  final Color backgroundColor;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 9.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: AppText(
        label,
        color: textColor,
        fontSize: 11.sp,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}
