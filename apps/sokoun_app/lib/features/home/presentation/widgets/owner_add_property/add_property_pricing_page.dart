import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_add_property_content.dart';

import 'add_property_chip_wrap.dart';
import 'add_property_field.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyPricingPage extends StatelessWidget {
  const AddPropertyPricingPage({
    super.key,
    required this.onNext,
    required this.onBack,
  });

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      title: 'التسعير والتفاصيل',
      activeSegments: 3,
      progressSubtitle: 'الخطوة 3 من 4 — السعر والتفاصيل',
      primaryLabel: 'التالي — التفاصيل الإضافية',
      onPrimaryTap: onNext,
      onBack: onBack,
      children: const [
        _PriceSection(),
        _RentalPeriodSection(),
        AddPropertySectionCard(
          title: 'المرافق والخدمات',
          child: AddPropertyChipWrap(chips: OwnerAddPropertyContent.amenities),
        ),
        _DescriptionSection(),
        AddPropertyInfoBanner(
          text: 'رسوم المنصة يتم خصمها من أرباح المالك حسب سياسة سكون',
          backgroundColor: AppColors.amberPale,
          borderColor: AppColors.goldAlpha15,
          iconColor: AppColors.brown,
          textColor: AppColors.brown,
          icon: Icons.info_outline_rounded,
        ),
      ],
    );
  }
}

class _PriceSection extends StatelessWidget {
  const _PriceSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'السعر',
      child: Column(
        children: [
          AddPropertyField(
            field: OwnerAddPropertyContent.pricingFields[0],
            suffix: AppText(
              'ر.س',
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w700,
            ),
          ),
          10.szH,
          AddPropertyField(field: OwnerAddPropertyContent.pricingFields[1]),
        ],
      ),
    );
  }
}

class _RentalPeriodSection extends StatelessWidget {
  const _RentalPeriodSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'فترة التأجير',
      child: Column(
        children: [
          Row(
            textDirection: TextDirection.ltr,
            children: [
              Expanded(
                child: AddPropertyField(
                  field: AddPropertyFieldContent(
                    label: 'العدد',
                    value: '6',
                    isFocused: true,
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
              10.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    AppText(
                      'الوحدة',
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w600,
                      textAlign: TextAlign.right,
                    ),
                    6.szH,
                    Container(
                      height: 46.h,
                      padding: EdgeInsets.symmetric(horizontal: 12.w),
                      decoration: BoxDecoration(
                        color: AppColors.tealAlpha03,
                        borderRadius: BorderRadius.circular(12.r),
                        border: Border.all(color: AppColors.sokoonTeal),
                      ),
                      child: Row(
                        textDirection: TextDirection.ltr,
                        children: [
                          Icon(
                            Icons.keyboard_arrow_down_rounded,
                            color: AppColors.sokoonTeal,
                            size: 20.r,
                          ),
                          const Spacer(),
                          AppText(
                            'شهر',
                            color: AppColors.sokoonTeal,
                            fontSize: 15.sp,
                            fontWeight: FontWeight.w900,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          12.szH,
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
            decoration: BoxDecoration(
              color: AppColors.tealAlpha03,
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: AppText(
              'فترة التأجير: 6 شهر',
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}

class _DescriptionSection extends StatelessWidget {
  const _DescriptionSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'وصف العقار',
      child: Container(
        height: 86.h,
        padding: EdgeInsets.all(12.w),
        decoration: BoxDecoration(
          color: AppColors.grayOffWhite,
          borderRadius: BorderRadius.circular(12.r),
          border: Border.all(color: AppColors.grayPale),
        ),
        alignment: AlignmentDirectional.topStart,
        child: AppText(
          'اكتب وصفاً جذاباً للعقار…',
          color: AppColors.navyAlpha50,
          fontSize: 12.sp,
          fontWeight: FontWeight.w400,
          textAlign: TextAlign.right,
        ),
      ),
    );
  }
}
