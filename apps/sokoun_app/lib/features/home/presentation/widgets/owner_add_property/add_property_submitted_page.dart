import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_add_property_content.dart';

import 'add_property_primary_button.dart';

class AddPropertySubmittedPage extends StatelessWidget {
  const AddPropertySubmittedPage({super.key, required this.onAddAnother});

  final VoidCallback onAddAnother;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 32.w),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              width: 96.r,
              height: 96.r,
              alignment: Alignment.center,
              margin: EdgeInsets.symmetric(horizontal: 98.w),
              decoration: const BoxDecoration(
                color: AppColors.orangePale,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.schedule_rounded,
                color: AppColors.amber,
                size: 42.r,
              ),
            ),
            16.szH,
            Center(
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: AppColors.orangePale,
                  borderRadius: BorderRadius.circular(999.r),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.schedule_rounded,
                      color: AppColors.amber,
                      size: 12.r,
                    ),
                    4.szW,
                    AppText(
                      'قيد المراجعة',
                      color: AppColors.amber,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w600,
                    ),
                  ],
                ),
              ),
            ),
            14.szH,
            AppText(
              'تم إرسال العقار للمراجعة',
              color: AppColors.sokoonNavy,
              fontSize: 23.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            8.szH,
            AppText(
              'فريقنا هيراجع عقارك خلال 24-48 ساعة وهتلاقي النتيجة في الإشعارات.',
              color: AppColors.sokoonGray,
              fontSize: 14.sp,
              fontWeight: FontWeight.w400,
              textAlign: TextAlign.center,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            22.szH,
            const _SubmittedSummaryCard(),
            22.szH,
            AddPropertyPrimaryButton(label: 'عرض عقاراتي', onTap: () {}),
            12.szH,
            AddPropertyPrimaryButton(
              label: 'إضافة عقار آخر',
              isOutline: true,
              onTap: onAddAnother,
            ),
          ],
        ),
      ),
    );
  }
}

class _SubmittedSummaryCard extends StatelessWidget {
  const _SubmittedSummaryCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(18.r),
        border: Border.all(color: AppColors.sokoonBorder),
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
          for (
            int index = 0;
            index < OwnerAddPropertyContent.submittedSummary.length;
            index++
          ) ...[
            _SummaryRow(item: OwnerAddPropertyContent.submittedSummary[index]),
            if (index < OwnerAddPropertyContent.submittedSummary.length - 1)
              const Divider(color: AppColors.sokoonBorder),
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
    return SizedBox(
      height: 34.h,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          AppText(
            item.value,
            color: AppColors.sokoonNavy,
            fontSize: 13.sp,
            fontWeight: FontWeight.w900,
          ),
          const Spacer(),
          AppText(
            item.label,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
          ),
        ],
      ),
    );
  }
}
