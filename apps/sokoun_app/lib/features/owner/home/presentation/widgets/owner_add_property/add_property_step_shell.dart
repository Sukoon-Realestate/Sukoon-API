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
    required this.title,
    required this.children,
    required this.primaryLabel,
    required this.activeSegments,
    this.onPrimaryTap,
    this.progressSubtitle,
    this.segmentCount = 4,
    this.onBack,
    this.secondaryLabel,
    this.onSecondaryTap,
  });

  final String title;
  final List<Widget> children;
  final String primaryLabel;
  final VoidCallback? onPrimaryTap;
  final int activeSegments;
  final String? progressSubtitle;
  final int segmentCount;
  final VoidCallback? onBack;
  final String? secondaryLabel;
  final VoidCallback? onSecondaryTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _TopBar(title: title, onBack: onBack),
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
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w400,
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

class _TopBar extends StatelessWidget {
  const _TopBar({required this.title, this.onBack});

  final String title;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minHeight: 64.h),
      padding: EdgeInsets.symmetric(horizontal: 16.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: onBack,
            behavior: HitTestBehavior.opaque,
            child: Container(
              width: 48.r,
              height: 48.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.grayBackground,
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Icon(
                Icons.chevron_left_rounded,
                color: AppColors.sokoonNavy,
                size: 22.r,
              ),
            ),
          ),
          8.szW,
          Expanded(
            child: AppText(
              title,
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              fontWeight: FontWeight.w700,
              textAlign: TextAlign.center,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          8.szW,
          SizedBox(width: 48.r),
        ],
      ),
    );
  }
}
