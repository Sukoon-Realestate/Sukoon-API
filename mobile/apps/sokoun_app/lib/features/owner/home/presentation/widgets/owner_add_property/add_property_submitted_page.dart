import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_primary_button.dart';

class AddPropertySubmittedPage extends StatelessWidget {
  const AddPropertySubmittedPage({
    super.key,
    this.message = '',
    required this.summaryItems,
    required this.onAddAnother,
  });

  final List<AddPropertySummaryContent> summaryItems;
  final String message;
  final VoidCallback onAddAnother;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: ListView(
        padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 24.h),
        children: [
          SokounReveal(
            beginScale: .88,
            child: Container(
              width: 96.r,
              height: 96.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: context.appColor(AppColors.orangePale, surface: true),
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.schedule_rounded,
                color: context.appColor(AppColors.brown),
                size: 42.r,
              ),
            ),
          ).centerWidget,
          16.szH,
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.orangePale, surface: true),
              borderRadius: BorderRadius.circular(999.r),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              spacing: 4.w,
              children: [
                Icon(
                  Icons.schedule_rounded,
                  color: context.appColor(AppColors.brown),
                  size: 12.r,
                ),
                AppText(
                  LocaleKeys.ownerPropertySubmittedStatus,
                  style: AppTextStyles.semiBold.copyWith(
                    color: context.appColor(AppColors.brown),
                    fontSize: 12.sp,
                  ),
                ),
              ],
            ),
          ).centerWidget,
          14.szH,
          AppText(
            message,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 23.sp,
            ),
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            LocaleKeys.ownerPropertySubmittedDescription,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 14.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          22.szH,
          SokounReveal(
            delay: const Duration(milliseconds: 80),
            child: _SubmittedSummaryCard(items: summaryItems),
          ),
          22.szH,
          AddPropertyPrimaryButton(
            label: LocaleKeys.ownerPropertySubmittedViewProperties,
            onTap: () => Go.back(true),
          ),
          12.szH,
          AddPropertyPrimaryButton(
            label: LocaleKeys.ownerPropertySubmittedAddAnother,
            isOutline: true,
            onTap: onAddAnother,
          ),
        ],
      ),
    );
  }
}

class _SubmittedSummaryCard extends StatelessWidget {
  const _SubmittedSummaryCard({required this.items});

  final List<AddPropertySummaryContent> items;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowBlack04,
            blurRadius: 4,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          for (int index = 0; index < items.length; index++) ...[
            _SummaryRow(item: items[index]),
            if (index < items.length - 1)
              Divider(color: context.appColor(AppColors.sokoonBorder)),
          ],
        ],
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.item});

  final AddPropertySummaryContent item;

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: BoxConstraints(minHeight: 40.h),
      child: Row(
        spacing: 10.w,
        children: [
          Expanded(
            flex: 3,
            child: AppText(
              item.value,
              style: AppTextStyles.bold13.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 13.sp,
                height: 1.45,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.start,
            ),
          ),
          Expanded(
            flex: 2,
            child: AppText(
              item.label,
              style: AppTextStyles.regular12.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 12.sp,
                height: 1.45,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.end,
            ),
          ),
        ],
      ).paddingSymmetric(vertical: 4.h),
    );
  }
}
