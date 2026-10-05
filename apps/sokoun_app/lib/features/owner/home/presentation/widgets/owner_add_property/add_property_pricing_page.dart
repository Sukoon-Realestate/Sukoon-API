import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_chip_wrap.dart';
import 'property_selection_field.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_filter_options_cubit.dart';
import 'add_property_options_empty_state.dart';
import 'add_property_field.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';
import 'add_property_additional_details.dart';

class AddPropertyPricingPage extends StatefulWidget {
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
    this.onOptionLabelsLoaded,
    required this.onAdditionalDetailsChanged,
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
  final ValueChanged<Map<String, String>>? onOptionLabelsLoaded;
  final ValueChanged<OwnerAddPropertyFormState> onAdditionalDetailsChanged;

  @override
  State<AddPropertyPricingPage> createState() => _AddPropertyPricingPageState();
}

class _AddPropertyPricingPageState extends State<AddPropertyPricingPage> {
  late final PropertyFilterOptionsCubit _optionsCubit;
  @override
  void initState() {
    super.initState();
    _optionsCubit = PropertyFilterOptionsCubit();
    _loadOptions();
  }

  Future<void> _loadOptions() => _optionsCubit.getFilterOptions(
    onLoaded: (options) {
      if (!mounted) return;
      widget.onOptionLabelsLoaded?.call({
        'amenity:furnished': LocaleKeys.ownerAddPropertyFurnished,
        for (final option in options.amenities)
          'amenity:${option.value}': option.label,
        for (final option in options.suitableFor)
          'suitable_for:${option.value}': option.label,
        for (final option in options.pricePeriods)
          'price_period:${option.value}': option.label,
      });
    },
  );

  @override
  void dispose() {
    _optionsCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AddPropertyStepShell(
      activeSegments: 3,
      segmentCount: 3,
      progressSubtitle: LocaleKeys.ownerAddPropertyPricingProgress,
      primaryLabel: widget.isSubmitting
          ? LocaleKeys.ownerAddPropertySubmitting
          : LocaleKeys.ownerPropertyReviewAction,
      onPrimaryTap: !widget.isSubmitting ? widget.onNext : null,
      children: [
        _PriceSection(
          form: widget.form,
          monthlyPriceController: widget.monthlyPriceController,
          onMonthlyPriceChanged: widget.onMonthlyPriceChanged,
        ),
        BlocProvider<PropertyFilterOptionsCubit>.value(
          value: _optionsCubit,
          child:
              StatusBuilder<
                PropertyFilterOptionsCubit,
                PropertyFilterOptionsModel
              >.withShimmer(
                initialDataForShimmer:
                    const PropertyFilterOptionsModel.initial(),
                onRetry: _loadOptions,
                shimmerBuilder: (_) => const SizedBox(height: 120),
                builder: (options) {
                  if (options.pricePeriods.isEmpty &&
                      options.suitableFor.isEmpty &&
                      options.amenities.isEmpty) {
                    return const AddPropertyOptionsEmptyState();
                  }
                  return Column(
                    spacing: 16,
                    children: [
                      _RentalPeriodSection(
                        form: widget.form,
                        rentalDurationController:
                            widget.rentalDurationController,
                        onRentalDurationChanged: widget.onRentalDurationChanged,
                        onRentalUnitChanged: widget.onRentalUnitChanged,
                        options: options.pricePeriods,
                      ),
                      AddPropertySectionCard(
                        title: LocaleKeys.ownerAddPropertyAmenities,
                        child: AddPropertyChipWrap(
                          chips: [
                            AddPropertyChipContent(
                              label: LocaleKeys.ownerAddPropertyFurnished,
                              value: 'furnished',
                              isSelected: widget.form.amenityApiValues.contains(
                                'furnished',
                              ),
                            ),
                            for (final option in options.amenities)
                              AddPropertyChipContent(
                                label: option.label,
                                value: option.value,
                                isSelected: widget.form.amenityApiValues
                                    .contains(option.value),
                              ),
                            for (final value in widget.form.amenityApiValues)
                              if (value != 'furnished' &&
                                  !options.amenities.any(
                                    (option) => option.value == value,
                                  ))
                                AddPropertyChipContent(
                                  label:
                                      widget
                                          .form
                                          .optionLabels['amenity:$value'] ??
                                      value,
                                  value: value,
                                  isSelected: true,
                                ),
                          ],
                          onChipTap: (chip) =>
                              widget.onAmenityToggled(chip.selectionValue),
                        ),
                      ),
                      AddPropertySectionCard(
                        title: '${LocaleKeys.ownerAddPropertySuitableFor} *',
                        child: options.suitableFor.isEmpty
                            ? const AddPropertyOptionsEmptyState()
                            : PropertySelectionField(
                                isValid:
                                    widget.form.suitableForApiValue.isNotEmpty,
                                child: AddPropertyChipWrap(
                                  chips: [
                                    for (final option in options.suitableFor)
                                      AddPropertyChipContent(
                                        label: option.label,
                                        value: option.value,
                                        isSelected:
                                            widget.form.suitableForApiValue ==
                                            option.value,
                                      ),
                                  ],
                                  onChipTap: (chip) =>
                                      widget.onSuitableForSelected(
                                        chip.selectionValue,
                                      ),
                                ),
                              ),
                      ),
                    ],
                  );
                },
              ),
        ),
        _DescriptionSection(
          descriptionController: widget.descriptionController,
          onDescriptionChanged: widget.onDescriptionChanged,
        ),
        AddPropertyAdditionalDetails(
          form: widget.form,
          onDetailsChanged: widget.onAdditionalDetailsChanged,
        ),
        AddPropertyInfoBanner(
          text: widget.form.isPricingReady
              ? LocaleKeys.ownerAddPropertyPricingReady
              : LocaleKeys.ownerAddPropertyPricingRequired,
          backgroundColor: widget.form.isPricingReady
              ? AppColors.greenPale
              : AppColors.amberPale,
          borderColor: widget.form.isPricingReady
              ? AppColors.greenAlpha19
              : AppColors.goldAlpha15,
          iconColor: widget.form.isPricingReady
              ? AppColors.green
              : AppColors.brown,
          textColor: widget.form.isPricingReady
              ? AppColors.sokoonNavy
              : AppColors.brown,
          icon: widget.form.isPricingReady
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
            validator: (value) => Validators.isPositiveNumber(value ?? '')
                ? null
                : LocaleKeys.propertyPositiveNumber,
            controller: monthlyPriceController,
            onChanged: onMonthlyPriceChanged,
            keyboardType: TextInputType.number,
            inputFormatters: [const LocalizedDigitsFormatter()],
            suffix: AppText(
              EgyptianPoundText.symbol,
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
    required this.options,
  });

  final OwnerAddPropertyFormState form;
  final List<TenantFilterOption> options;
  final TextEditingController rentalDurationController;
  final ValueChanged<String> onRentalDurationChanged;
  final ValueChanged<String> onRentalUnitChanged;

  @override
  Widget build(BuildContext context) {
    final selected = options
        .where((option) => option.value == form.rentalUnitApiValue)
        .firstOrNull;
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
                  validator: (value) => Validators.isPositiveNumber(value ?? '')
                      ? null
                      : LocaleKeys.propertyPositiveNumber,
                  controller: rentalDurationController,
                  onChanged: onRentalDurationChanged,
                  keyboardType: TextInputType.number,
                  inputFormatters: [const LocalizedDigitsFormatter()],
                ),
              ),
              Expanded(
                child: DropdownButtonFormField<TenantFilterOption>(
                  isExpanded: true,
                  validator: (_) =>
                      Validators.validateRequired(form.rentalUnitApiValue),
                  decoration: InputDecoration(
                    labelText: '${LocaleKeys.ownerAddPropertyUnit} *',
                  ),
                  hint: AppText(LocaleKeys.ownerAddPropertyChoose),
                  initialValue: selected,
                  items: [
                    for (final option in options)
                      DropdownMenuItem(
                        value: option,
                        child: AppText(option.label),
                      ),
                  ],
                  onChanged: (option) {
                    if (option != null) onRentalUnitChanged(option.value);
                  },
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
                  .replaceAll('{unit}', selected?.label ?? form.rentalUnit),
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
        validator: (value) => Validators.hasMinimumLength(value ?? '', 10)
            ? null
            : LocaleKeys.propertyDescriptionMinimum,
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
