import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

class VisitSlotChip extends StatelessWidget {
  const VisitSlotChip({
    super.key,
    required this.slot,
    required this.isSelected,
    required this.onTap,
  });

  final TenantVisitSlotContent slot;
  final bool isSelected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final isEnabled = onTap != null;
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected
              ? AppColors.sokoonTeal
              : isEnabled
              ? AppColors.white
              : AppColors.grayBackground,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(
            color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
          ),
        ),
        child: AppText(
          slot.label,
          color: isSelected
              ? AppColors.white
              : isEnabled
              ? AppColors.sokoonNavy
              : AppColors.sokoonMuted,
          fontSize: 13.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
