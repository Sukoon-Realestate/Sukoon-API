import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';

import 'add_property_address_section.dart';
import 'add_property_chip_wrap.dart';
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
    required this.selectedGovernorate,
    required this.selectedCity,
    required this.locationDropdownGeneration,
    required this.onPropertyTypeSelected,
    required this.onTitleChanged,
    required this.onGovernorateChanged,
    required this.onCityChanged,
    required this.onStreetChanged,
    required this.onBedroomsChanged,
    required this.onBathroomsChanged,
    required this.onSpaceChanged,
    required this.onFloorChanged,
    required this.onBuildingYearChanged,
    required this.onMapQueryChanged,
    required this.onLocationSelected,
    required this.onNext,
    this.title,
    this.onBack,
  });

  final String? title;
  final OwnerAddPropertyFormState form;
  final TextEditingController titleController;
  final TextEditingController streetController;
  final TextEditingController bedroomsController;
  final TextEditingController bathroomsController;
  final TextEditingController spaceController;
  final TextEditingController floorController;
  final TextEditingController buildingYearController;
  final TextEditingController mapQueryController;
  final OwnerPropertyLocationModel? selectedGovernorate;
  final OwnerPropertyLocationModel? selectedCity;
  final int locationDropdownGeneration;
  final ValueChanged<String> onPropertyTypeSelected;
  final ValueChanged<String> onTitleChanged;
  final ValueChanged<OwnerPropertyLocationModel> onGovernorateChanged;
  final ValueChanged<OwnerPropertyLocationModel> onCityChanged;
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
      title: title ?? LocaleKeys.ownerAddPropertyTitle,
      activeSegments: 1,
      segmentCount: 5,
      progressSubtitle: LocaleKeys.ownerAddPropertyBasicsProgress,
      primaryLabel: LocaleKeys.ownerAddPropertyNextPhotos,
      onPrimaryTap: form.isBasicsReady ? onNext : null,
      onBack: onBack,
      children: [
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertyType,
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.singleSelectedChips(
              labels: OwnerAddPropertyContent.propertyTypeOptions,
              selectedValue: form.propertyType,
            ),
            onChipTap: (chip) => onPropertyTypeSelected(chip.label),
          ),
        ),
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertyNameSection,
          child: AddPropertyField(
            field: AddPropertyFieldContent(
              label: LocaleKeys.ownerAddPropertyTitleLabel,
              value: LocaleKeys.ownerAddPropertyTitleExample,
            ),
            controller: titleController,
            onChanged: onTitleChanged,
            hint: LocaleKeys.ownerAddPropertyTitleHint,
          ),
        ),
        AddPropertyAddressSection(
          streetController: streetController,
          selectedGovernorate: selectedGovernorate,
          selectedCity: selectedCity,
          dropdownGeneration: locationDropdownGeneration,
          onGovernorateChanged: onGovernorateChanged,
          onCityChanged: onCityChanged,
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
        label: LocaleKeys.ownerAddPropertyBedrooms,
        controller: bedroomsController,
        onChanged: onBedroomsChanged,
      ),
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertyBathrooms,
        controller: bathroomsController,
        onChanged: onBathroomsChanged,
      ),
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertySpace,
        controller: spaceController,
        onChanged: onSpaceChanged,
      ),
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertyFloor,
        controller: floorController,
        onChanged: onFloorChanged,
      ),
      _NumberFieldConfig(
        label: LocaleKeys.ownerAddPropertyBuildingYear,
        controller: buildingYearController,
        onChanged: onBuildingYearChanged,
      ),
    ];

    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyDetails,
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
      title: LocaleKeys.ownerAddPropertyMapTitle,
      subtitle: LocaleKeys.ownerAddPropertyMapSubtitle,
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
                      hintText: LocaleKeys.ownerAddPropertyMapSearch,
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
                        ? LocaleKeys.ownerAddPropertyLocationSelected
                        : LocaleKeys.ownerAddPropertySelectLocation,
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
              title: LocaleKeys.ownerAddPropertySelectedLocation,
              text: form.mapQuery,
              backgroundColor: AppColors.greenPale,
              borderColor: AppColors.greenAlpha19,
              iconColor: AppColors.green,
              icon: Icons.location_on_outlined,
            )
          else
            AddPropertyInfoBanner(
              text: LocaleKeys.ownerAddPropertyLocationPrivacy,
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
