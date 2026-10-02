import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_chip_wrap.dart';
import 'add_property_dropdown_field.dart';
import 'add_property_field.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';

class AddPropertyPricingPage extends StatelessWidget {
  const AddPropertyPricingPage({
    super.key,
    required this.form,
    required this.monthlyPriceController,
    required this.rentalDurationController,
    required this.descriptionController,
    required this.onMonthlyPriceChanged,
    required this.onSuitableForSelected,
    required this.onRentalDurationChanged,
    required this.onRentalUnitChanged,
    required this.onAmenityToggled,
    required this.onDescriptionChanged,
    required this.onNext,
    this.isSubmitting = false,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController monthlyPriceController;
  final TextEditingController rentalDurationController;
  final TextEditingController descriptionController;
  final ValueChanged<String> onMonthlyPriceChanged;
  final ValueChanged<String> onSuitableForSelected;
  final ValueChanged<String> onRentalDurationChanged;
  final ValueChanged<String> onRentalUnitChanged;
  final ValueChanged<String> onAmenityToggled;
  final ValueChanged<String> onDescriptionChanged;
  final VoidCallback onNext;
  final bool isSubmitting;

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      activeSegments: 3,
      segmentCount: 3,
      progressSubtitle: LocaleKeys.ownerAddPropertyPricingProgress,
      primaryLabel: isSubmitting
          ? LocaleKeys.ownerAddPropertySubmitting
          : LocaleKeys.ownerPropertyReviewAction,
      onPrimaryTap: form.isPricingReady && !isSubmitting ? onNext : null,
      children: [
        _PriceSection(
          form: form,
          monthlyPriceController: monthlyPriceController,
          onMonthlyPriceChanged: onMonthlyPriceChanged,
        ),
        _RentalPeriodSection(
          form: form,
          rentalDurationController: rentalDurationController,
          onRentalDurationChanged: onRentalDurationChanged,
          onRentalUnitChanged: onRentalUnitChanged,
        ),
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertyAmenities,
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.multiSelectedChips(
              labels: OwnerAddPropertyContent.amenityOptions,
              selectedValues: form.amenities,
            ),
            onChipTap: (chip) => onAmenityToggled(chip.label),
          ),
        ),
        AddPropertySectionCard(
          title: LocaleKeys.ownerAddPropertySuitableFor,
          child: AddPropertyChipWrap(
            chips: OwnerAddPropertyContent.singleSelectedChips(
              labels: OwnerAddPropertyContent.suitableForOptions,
              selectedValue: form.suitableFor,
            ),
            onChipTap: (chip) => onSuitableForSelected(chip.label),
          ),
        ),
        _DescriptionSection(
          descriptionController: descriptionController,
          onDescriptionChanged: onDescriptionChanged,
        ),
        AddPropertyInfoBanner(
          text: form.isPricingReady
              ? LocaleKeys.ownerAddPropertyPricingReady
              : LocaleKeys.ownerAddPropertyPricingRequired,
          backgroundColor: form.isPricingReady
              ? AppColors.greenPale
              : AppColors.amberPale,
          borderColor: form.isPricingReady
              ? AppColors.greenAlpha19
              : AppColors.goldAlpha15,
          iconColor: form.isPricingReady ? AppColors.green : AppColors.brown,
          textColor: form.isPricingReady
              ? AppColors.sokoonNavy
              : AppColors.brown,
          icon: form.isPricingReady
              ? Icons.check_circle_outline_rounded
              : Icons.info_outline_rounded,
        ),
      ],
    );
  }
}

class _PriceSection extends StatelessWidget {
  const _PriceSection({
    required this.form,
    required this.monthlyPriceController,
    required this.onMonthlyPriceChanged,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController monthlyPriceController;
  final ValueChanged<String> onMonthlyPriceChanged;

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyPrice,
      child: Column(
        spacing: 10.h,
        children: [
          AddPropertyField(
            field: AddPropertyFieldContent(
              label: LocaleKeys.ownerAddPropertyPrice,
              value: '0',
              isFocused: true,
              textAlign: TextAlign.start,
            ),
            controller: monthlyPriceController,
            onChanged: onMonthlyPriceChanged,
            keyboardType: TextInputType.number,
            inputFormatters: [const LocalizedDigitsFormatter()],
            suffix: AppText(
              LocaleKeys.ownerAddPropertyCurrency,
              style: AppTextStyles.bold13.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 13.sp,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _RentalPeriodSection extends StatelessWidget {
  const _RentalPeriodSection({
    required this.form,
    required this.rentalDurationController,
    required this.onRentalDurationChanged,
    required this.onRentalUnitChanged,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController rentalDurationController;
  final ValueChanged<String> onRentalDurationChanged;
  final ValueChanged<String> onRentalUnitChanged;

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyRentalPeriod,
      child: Column(
        spacing: 12.h,
        children: [
          Row(
            spacing: 10.w,
            children: [
              Expanded(
                child: AddPropertyField(
                  field: AddPropertyFieldContent(
                    label: LocaleKeys.ownerAddPropertyCount,
                    value: '0',
                    isFocused: true,
                    textAlign: TextAlign.center,
                  ),
                  controller: rentalDurationController,
                  onChanged: onRentalDurationChanged,
                  keyboardType: TextInputType.number,
                  inputFormatters: [const LocalizedDigitsFormatter()],
                ),
              ),
              Expanded(
                child: AddPropertyDropdownField(
                  label: LocaleKeys.ownerAddPropertyUnit,
                  value: form.rentalUnit,
                  items: OwnerAddPropertyContent.rentalUnitOptions,
                  onChanged: onRentalUnitChanged,
                ),
              ),
            ],
          ),
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
            decoration: BoxDecoration(
              color: AppColors.tealAlpha03,
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: AppText(
              LocaleKeys.ownerAddPropertyRentalSummary
                  .replaceAll('{count}', form.rentalDuration)
                  .replaceAll('{unit}', form.rentalUnit),
              style: AppTextStyles.bold12.copyWith(
                color: AppColors.sokoonTeal,
                fontSize: 12.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.start,
            ),
          ),
        ],
      ),
    );
  }
}

class _DescriptionSection extends StatelessWidget {
  const _DescriptionSection({
    required this.descriptionController,
    required this.onDescriptionChanged,
  });

  final TextEditingController descriptionController;
  final ValueChanged<String> onDescriptionChanged;

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyDescription,
      child: AddPropertyField(
        field: AddPropertyFieldContent(
          label: LocaleKeys.ownerAddPropertyDescriptionLabel,
          value: LocaleKeys.ownerAddPropertyDescriptionHint,
        ),
        controller: descriptionController,
        onChanged: onDescriptionChanged,
        hint: LocaleKeys.ownerAddPropertyDescriptionHint,
        keyboardType: TextInputType.multiline,
        maxLines: 4,
        minLines: 4,
      ),
    );
  }
}
