import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_add_property_content.dart';

import 'add_property_chip_wrap.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyExtraDetailsPage extends StatelessWidget {
  const AddPropertyExtraDetailsPage({
    super.key,
    required this.onNext,
    required this.onBack,
  });

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      title: 'تفاصيل العقار',
      activeSegments: 4,
      progressSubtitle: 'الخطوة 4 من 4 — التفاصيل الإضافية',
      primaryLabel: 'التالي',
      onPrimaryTap: onNext,
      onBack: onBack,
      children: const [
        AddPropertySectionCard(
          title: 'التدخين مسموح؟',
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.smokingOptions,
          ),
        ),
        AddPropertySectionCard(
          title: 'العقار مناسب لـ',
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.suitableFor,
          ),
        ),
        _OwnershipProofSection(),
      ],
    );
  }
}

class _OwnershipProofSection extends StatelessWidget {
  const _OwnershipProofSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'إثبات ملكية العقار',
      subtitle: 'ممكن ترفع وصل كهربا، وصل مياه، أو عقد الملكية',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 22.h),
            decoration: BoxDecoration(
              color: AppColors.grayOffWhite,
              borderRadius: BorderRadius.circular(12.r),
              border: Border.all(color: AppColors.grayPale, width: 1.2),
            ),
            child: Column(
              children: [
                Icon(
                  Icons.cloud_upload_outlined,
                  color: AppColors.sokoonGray,
                  size: 30.r,
                ),
                8.szH,
                AppText(
                  'ارفع إثبات الملكية',
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w800,
                ),
                4.szH,
                AppText(
                  'PDF · JPG · PNG',
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w500,
                ),
              ],
            ),
          ),
          10.szH,
          const AddPropertyInfoBanner(
            title: 'المستند ده للمراجعة الداخلية فقط',
            text: 'ومش هيظهر للمستخدمين أو المستأجرين',
            icon: Icons.lock_outline_rounded,
          ),
          10.szH,
          const AddPropertyChipWrap(chips: OwnerAddPropertyContent.proofStates),
        ],
      ),
    );
  }
}
