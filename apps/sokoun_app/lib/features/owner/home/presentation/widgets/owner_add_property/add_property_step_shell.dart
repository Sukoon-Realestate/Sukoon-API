import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import 'add_property_primary_button.dart';

class AddPropertyStepShell extends StatelessWidget {
  const AddPropertyStepShell({
    super.key,
    required this.children,
    required this.primaryLabel,
    required this.activeSegments,
    this.onPrimaryTap,
    this.progressSubtitle,
    this.segmentCount = 4,
    this.secondaryLabel,
    this.onSecondaryTap,
  });

  final List<Widget> children;
  final String primaryLabel;
  final VoidCallback? onPrimaryTap;
  final int activeSegments;
  final String? progressSubtitle;
  final int segmentCount;
  final String? secondaryLabel;
  final VoidCallback? onSecondaryTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
          decoration: const BoxDecoration(
            color: AppColors.white,
            border: Border(bottom: BorderSide(color: AppColors.grayPale)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  for (int index = 0; index < segmentCount; index++) ...[
                    Expanded(
                      child: AnimatedContainer(
                        duration: SokounMotion.duration(context),
                        height: 4.h,
                        decoration: BoxDecoration(
                          color: index < activeSegments
                              ? AppColors.sokoonTeal
                              : AppColors.grayPale,
                          borderRadius: BorderRadius.circular(999.r),
                        ),
                      ),
                    ),
                    if (index < segmentCount - 1) 6.szW,
                  ],
                ],
              ),
              if (progressSubtitle != null) ...[
                8.szH,
                AppText(
                  progressSubtitle!,
                  style: AppTextStyles.regular11.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    height: 1.45,
                  ),
                  textAlign: TextAlign.start,
                ),
              ],
            ],
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: EdgeInsets.all(16.w),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                for (int index = 0; index < children.length; index++) ...[
                  children[index],
                  if (index < children.length - 1) 12.szH,
                ],
                24.szH,
              ],
            ),
          ),
        ),
        SokounActionFooter(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AddPropertyPrimaryButton(
                label: primaryLabel,
                onTap: onPrimaryTap,
              ),
              if (secondaryLabel != null) ...[
                10.szH,
                AddPropertyPrimaryButton(
                  label: secondaryLabel!,
                  isOutline: true,
                  onTap: onSecondaryTap,
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
