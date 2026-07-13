import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_request_content.dart';

class OwnerRequestTabs extends StatelessWidget {
  const OwnerRequestTabs({super.key, required this.tabs});

  final List<OwnerRequestTabContent> tabs;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          for (int index = 0; index < tabs.length; index++) ...[
            _OwnerRequestTab(tab: tabs[index]),
            if (index < tabs.length - 1) 8.szW,
          ],
        ],
      ),
    );
  }
}

class _OwnerRequestTab extends StatelessWidget {
  const _OwnerRequestTab({required this.tab});

  final OwnerRequestTabContent tab;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 34.h,
      padding: EdgeInsets.symmetric(horizontal: 14.w),
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: tab.isSelected ? AppColors.sokoonTeal : AppColors.white,
        borderRadius: BorderRadius.circular(999.r),
        border: Border.all(
          color: tab.isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
        ),
      ),
      child: AppText(
        tab.label,
        color: tab.isSelected ? AppColors.white : AppColors.sokoonNavy,
        fontSize: 12.sp,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}
