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

class AddPropertyBasicsPage extends StatelessWidget {
  const AddPropertyBasicsPage({super.key, required this.onNext, this.onBack});

  final VoidCallback onNext;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      title: 'إضافة عقار جديد',
      activeSegments: 1,
      progressSubtitle: 'الخطوة 1 من 4 — معلومات العقار',
      primaryLabel: 'التالي — الصور',
      onPrimaryTap: onNext,
      onBack: onBack,
      children: const [
        AddPropertySectionCard(
          title: 'نوع العقار',
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.propertyTypes,
          ),
        ),
        _AddressSection(),
        _DetailsSection(),
        _MapSection(),
      ],
    );
  }
}

class _AddressSection extends StatelessWidget {
  const _AddressSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'المنطقة والعنوان',
      child: Column(
        children: [
          for (
            int index = 0;
            index < OwnerAddPropertyContent.addressFields.length;
            index++
          ) ...[
            AddPropertyField(
              field: OwnerAddPropertyContent.addressFields[index],
            ),
            if (index < OwnerAddPropertyContent.addressFields.length - 1)
              10.szH,
          ],
        ],
      ),
    );
  }
}

class _DetailsSection extends StatelessWidget {
  const _DetailsSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'تفاصيل العقار',
      child: GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 2.2,
          crossAxisSpacing: 10.w,
          mainAxisSpacing: 10.h,
        ),
        itemCount: OwnerAddPropertyContent.detailFields.length,
        itemBuilder: (context, index) {
          return AddPropertyField(
            field: OwnerAddPropertyContent.detailFields[index],
          );
        },
      ),
    );
  }
}

class _MapSection extends StatelessWidget {
  const _MapSection();

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: 'موقع العقار على الخريطة',
      subtitle: 'حدد موقع العقار بدقة عشان نراجع الإعلان بشكل أسرع',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            height: 44.h,
            padding: EdgeInsets.symmetric(horizontal: 12.w),
            decoration: BoxDecoration(
              color: AppColors.grayOffWhite,
              borderRadius: BorderRadius.circular(10.r),
              border: Border.all(color: AppColors.grayPale),
            ),
            child: Row(
              textDirection: TextDirection.ltr,
              children: [
                Icon(
                  Icons.search_rounded,
                  color: AppColors.sokoonGray,
                  size: 18.r,
                ),
                8.szW,
                Expanded(
                  child: AppText(
                    'ابحث عن الموقع...',
                    color: AppColors.navyAlpha50,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w400,
                  ),
                ),
              ],
            ),
          ),
          12.szH,
          Container(
            height: 140.h,
            decoration: BoxDecoration(
              color: AppColors.mintPale,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Positioned.fill(
                  child: CustomPaint(painter: _MapPatternPainter()),
                ),
                Icon(
                  Icons.location_on_rounded,
                  color: AppColors.sokoonTeal,
                  size: 34.r,
                ),
              ],
            ),
          ),
          12.szH,
          Container(
            height: 44.h,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.sokoonTeal,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.my_location_rounded,
                  color: AppColors.white,
                  size: 17.r,
                ),
                8.szW,
                AppText(
                  'تحديد الموقع',
                  color: AppColors.white,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w900,
                ),
              ],
            ),
          ),
          10.szH,
          const AddPropertyInfoBanner(
            text: 'قد يظهر الموقع للمستأجرين بشكل تقريبي لحماية الخصوصية',
            icon: Icons.shield_outlined,
          ),
        ],
      ),
    );
  }
}

class _MapPatternPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final roadPaint = Paint()
      ..color = AppColors.whiteAlpha60
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    final blockPaint = Paint()
      ..color = AppColors.tealAlpha07
      ..style = PaintingStyle.fill;

    for (double x = -20; x < size.width; x += 46) {
      canvas.drawLine(Offset(x, 0), Offset(x + 54, size.height), roadPaint);
    }
    for (double y = 18; y < size.height; y += 42) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y - 18), roadPaint);
    }
    for (double x = 18; x < size.width; x += 70) {
      for (double y = 18; y < size.height; y += 54) {
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromLTWH(x, y, 22, 14),
            Radius.circular(4.r),
          ),
          blockPaint,
        );
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
