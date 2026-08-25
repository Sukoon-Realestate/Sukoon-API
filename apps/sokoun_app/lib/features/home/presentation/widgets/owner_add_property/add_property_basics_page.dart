import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_add_property_content.dart';

import 'add_property_chip_wrap.dart';
import 'add_property_dropdown_field.dart';
import 'add_property_field.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyBasicsPage extends StatelessWidget {
  const AddPropertyBasicsPage({
    super.key,
    required this.form,
    required this.titleController,
    required this.streetController,
    required this.bedroomsController,
    required this.bathroomsController,
    required this.spaceController,
    required this.floorController,
    required this.buildingYearController,
    required this.mapQueryController,
    required this.onPropertyTypeSelected,
    required this.onTitleChanged,
    required this.onGovernorateChanged,
    required this.onDistrictChanged,
    required this.onStreetChanged,
    required this.onBedroomsChanged,
    required this.onBathroomsChanged,
    required this.onSpaceChanged,
    required this.onFloorChanged,
    required this.onBuildingYearChanged,
    required this.onMapQueryChanged,
    required this.onLocationSelected,
    required this.onNext,
    this.onBack,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController titleController;
  final TextEditingController streetController;
  final TextEditingController bedroomsController;
  final TextEditingController bathroomsController;
  final TextEditingController spaceController;
  final TextEditingController floorController;
  final TextEditingController buildingYearController;
  final TextEditingController mapQueryController;
  final ValueChanged<String> onPropertyTypeSelected;
  final ValueChanged<String> onTitleChanged;
  final ValueChanged<String> onGovernorateChanged;
  final ValueChanged<String> onDistrictChanged;
  final ValueChanged<String> onStreetChanged;
  final ValueChanged<String> onBedroomsChanged;
  final ValueChanged<String> onBathroomsChanged;
  final ValueChanged<String> onSpaceChanged;
  final ValueChanged<String> onFloorChanged;
  final ValueChanged<String> onBuildingYearChanged;
  final ValueChanged<String> onMapQueryChanged;
  final VoidCallback onLocationSelected;
  final VoidCallback onNext;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      title: 'إضافة عقار جديد',
      activeSegments: 1,
      progressSubtitle: 'الخطوة 1 من 4 — معلومات العقار',
      primaryLabel: 'التالي — الصور',
      onPrimaryTap: form.isBasicsReady ? onNext : null,
      onBack: onBack,
      children: [
        AddPropertySectionCard(
          title: 'نوع العقار',
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.singleSelectedChips(
              labels: OwnerAddPropertyContent.propertyTypeOptions,
              selectedValue: form.propertyType,
            ),
            onChipTap: (chip) => onPropertyTypeSelected(chip.label),
          ),
        ),
        AddPropertySectionCard(
          title: 'عنوان العقار',
          child: AddPropertyField(
            field: const AddPropertyFieldContent(
              label: 'العنوان',
              value: 'مثال: شقة مفروشة قريبة من المترو',
            ),
            controller: titleController,
            onChanged: onTitleChanged,
            hint: 'اكتب عنواناً واضحاً للعقار',
          ),
        ),
        _AddressSection(
          form: form,
          streetController: streetController,
          onGovernorateChanged: onGovernorateChanged,
          onDistrictChanged: onDistrictChanged,
          onStreetChanged: onStreetChanged,
        ),
        _DetailsSection(
          bedroomsController: bedroomsController,
          bathroomsController: bathroomsController,
          spaceController: spaceController,
          floorController: floorController,
          buildingYearController: buildingYearController,
          onBedroomsChanged: onBedroomsChanged,
          onBathroomsChanged: onBathroomsChanged,
          onSpaceChanged: onSpaceChanged,
          onFloorChanged: onFloorChanged,
          onBuildingYearChanged: onBuildingYearChanged,
        ),
        _MapSection(
          form: form,
          mapQueryController: mapQueryController,
          onMapQueryChanged: onMapQueryChanged,
          onLocationSelected: onLocationSelected,
        ),
      ],
    );
  }
}

class _AddressSection extends StatelessWidget {
  const _AddressSection({
    required this.form,
    required this.streetController,
    required this.onGovernorateChanged,
    required this.onDistrictChanged,
    required this.onStreetChanged,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController streetController;
  final ValueChanged<String> onGovernorateChanged;
  final ValueChanged<String> onDistrictChanged;
  final ValueChanged<String> onStreetChanged;

  @override
  Widget build(BuildContext context) {
    final districts =
        OwnerAddPropertyContent.districtOptionsByGovernorate[form
            .governorate] ??
        const <String>[];

    return AddPropertySectionCard(
      title: 'المنطقة والعنوان',
      child: Column(
        children: [
          AddPropertyDropdownField(
            label: 'المحافظة',
            value: form.governorate,
            items: OwnerAddPropertyContent.governorateOptions,
            onChanged: onGovernorateChanged,
          ),
          10.szH,
          AddPropertyDropdownField(
            label: 'المنطقة',
            value: form.district,
            items: districts,
            onChanged: onDistrictChanged,
          ),
          10.szH,
          AddPropertyField(
            field: const AddPropertyFieldContent(
              label: 'الشارع',
              value: 'اكتب اسم الشارع',
            ),
            controller: streetController,
            onChanged: onStreetChanged,
            hint: 'اكتب اسم الشارع',
          ),
        ],
      ),
    );
  }
}

class _DetailsSection extends StatelessWidget {
  const _DetailsSection({
    required this.bedroomsController,
    required this.bathroomsController,
    required this.spaceController,
    required this.floorController,
    required this.buildingYearController,
    required this.onBedroomsChanged,
    required this.onBathroomsChanged,
    required this.onSpaceChanged,
    required this.onFloorChanged,
    required this.onBuildingYearChanged,
  });

  final TextEditingController bedroomsController;
  final TextEditingController bathroomsController;
  final TextEditingController spaceController;
  final TextEditingController floorController;
  final TextEditingController buildingYearController;
  final ValueChanged<String> onBedroomsChanged;
  final ValueChanged<String> onBathroomsChanged;
  final ValueChanged<String> onSpaceChanged;
  final ValueChanged<String> onFloorChanged;
  final ValueChanged<String> onBuildingYearChanged;

  @override
  Widget build(BuildContext context) {
    final fields = [
      _NumberFieldConfig(
        label: 'عدد الغرف',
        controller: bedroomsController,
        onChanged: onBedroomsChanged,
      ),
      _NumberFieldConfig(
        label: 'عدد الحمامات',
        controller: bathroomsController,
        onChanged: onBathroomsChanged,
      ),
      _NumberFieldConfig(
        label: 'المساحة (م²)',
        controller: spaceController,
        onChanged: onSpaceChanged,
      ),
      _NumberFieldConfig(
        label: 'الدور',
        controller: floorController,
        onChanged: onFloorChanged,
      ),
      _NumberFieldConfig(
        label: 'سنة البناء',
        controller: buildingYearController,
        onChanged: onBuildingYearChanged,
      ),
    ];

    return AddPropertySectionCard(
      title: 'تفاصيل العقار',
      child: GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 1.45,
          crossAxisSpacing: 10.w,
          mainAxisSpacing: 10.h,
        ),
        itemCount: fields.length,
        itemBuilder: (context, index) {
          final field = fields[index];
          return AddPropertyField(
            field: AddPropertyFieldContent(
              label: field.label,
              value: '0',
              textAlign: TextAlign.center,
            ),
            controller: field.controller,
            onChanged: field.onChanged,
            keyboardType: TextInputType.number,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
          );
        },
      ),
    );
  }
}

class _MapSection extends StatelessWidget {
  const _MapSection({
    required this.form,
    required this.mapQueryController,
    required this.onMapQueryChanged,
    required this.onLocationSelected,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController mapQueryController;
  final ValueChanged<String> onMapQueryChanged;
  final VoidCallback onLocationSelected;

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
                  child: TextField(
                    controller: mapQueryController,
                    onChanged: onMapQueryChanged,
                    textAlign: TextAlign.right,
                    style: TextStyle(
                      color: AppColors.sokoonNavy,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w600,
                    ),
                    decoration: InputDecoration(
                      isCollapsed: true,
                      border: InputBorder.none,
                      hintText: 'ابحث عن الموقع...',
                      hintStyle: TextStyle(
                        color: AppColors.navyAlpha50,
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
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
                  color: form.isLocationSelected
                      ? AppColors.green
                      : AppColors.sokoonTeal,
                  size: 34.r,
                ),
              ],
            ),
          ),
          12.szH,
          GestureDetector(
            onTap: onLocationSelected,
            behavior: HitTestBehavior.opaque,
            child: Container(
              height: 44.h,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: form.isLocationSelected
                    ? AppColors.green
                    : AppColors.sokoonTeal,
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    form.isLocationSelected
                        ? Icons.check_circle_outline_rounded
                        : Icons.my_location_rounded,
                    color: AppColors.white,
                    size: 17.r,
                  ),
                  8.szW,
                  AppText(
                    form.isLocationSelected
                        ? 'تم تحديد الموقع'
                        : 'تحديد الموقع',
                    color: AppColors.white,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w900,
                  ),
                ],
              ),
            ),
          ),
          10.szH,
          if (form.isLocationSelected)
            AddPropertyInfoBanner(
              title: 'الموقع المحدد',
              text: form.mapQuery,
              backgroundColor: AppColors.greenPale,
              borderColor: AppColors.greenAlpha19,
              iconColor: AppColors.green,
              icon: Icons.location_on_outlined,
            )
          else
            const AddPropertyInfoBanner(
              text: 'قد يظهر الموقع للمستأجرين بشكل تقريبي لحماية الخصوصية',
              icon: Icons.shield_outlined,
            ),
        ],
      ),
    );
  }
}

class _NumberFieldConfig {
  const _NumberFieldConfig({
    required this.label,
    required this.controller,
    required this.onChanged,
  });

  final String label;
  final TextEditingController controller;
  final ValueChanged<String> onChanged;
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
