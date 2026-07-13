import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_add_property_content.dart';

class AddPropertyChip extends StatelessWidget {
  const AddPropertyChip({
    super.key,
    required this.chip,
    this.showCheck = true,
    this.onTap,
  });

  final AddPropertyChipContent chip;
  final bool showCheck;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 34.h,
        padding: EdgeInsets.symmetric(horizontal: 14.w),
        decoration: BoxDecoration(
          color: chip.isSelected ? AppColors.tealAlpha07 : AppColors.white,
          borderRadius: BorderRadius.circular(999.r),
          border: Border.all(
            color: chip.isSelected ? AppColors.sokoonTeal : AppColors.grayPale,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (chip.isSelected && showCheck) ...[
              Icon(
                Icons.check_rounded,
                color: AppColors.sokoonTeal,
                size: 14.r,
              ),
              4.szW,
            ],
            AppText(
              chip.label,
              color: chip.isSelected
                  ? AppColors.sokoonTeal
                  : AppColors.sokoonNavy,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
            ),
          ],
        ),
      ),
    );
  }
}
