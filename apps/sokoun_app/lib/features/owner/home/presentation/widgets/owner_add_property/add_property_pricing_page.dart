import 'rental_offer_terms_editor.dart';
import 'property_selection_field.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_tenant_type.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';

import 'add_property_chip_wrap.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_filter_options_cubit.dart';
import 'add_property_field.dart';
import 'add_property_info_banner.dart';
import 'add_property_section_card.dart';
import 'add_property_step_shell.dart';
import 'add_property_additional_details.dart';
import 'add_property_rental_period_section.dart';
import 'property_form_validation.dart';

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
    this.listingAssistant,
    required this.onAdditionalDetailsChanged,
  });

  final Widget? listingAssistant;
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
  final GlobalKey _priceFieldKey = GlobalKey();
  final GlobalKey _durationFieldKey = GlobalKey();
  final GlobalKey _unitFieldKey = GlobalKey();
  final GlobalKey _amenitiesFieldKey = GlobalKey();
  final GlobalKey _suitableForFieldKey = GlobalKey();
  final GlobalKey _descriptionFieldKey = GlobalKey();
  final GlobalKey _buildingYearFieldKey = GlobalKey();
  final GlobalKey _depositFieldKey = GlobalKey();
  late final PropertyFilterOptionsCubit _optionsCubit;

  String get _unsupportedAmenitiesError => LocaleKeys
      .ownerPropertyUnsupportedAmenities
      .replaceAll('{items}', widget.form.unsupportedAmenities.join(', '));

  List<FirstValidationErrorField> _validationFields() =>
      widget.form.isPartialOffering
      ? [
          FirstValidationErrorField(
            fieldKey: _priceFieldKey,
            title: LocaleKeys.rentalOffers,
            value: null,
            validator: (_) => widget.form.isPricingReady
                ? null
                : LocaleKeys.rentalInvalidInventory,
          ),
        ]
      : [
          FirstValidationErrorField(
            fieldKey: _priceFieldKey,
            title: LocaleKeys.ownerAddPropertyPrice,
            value: widget.monthlyPriceController.text,
            validator: PropertyFormValidation.price,
          ),
          FirstValidationErrorField(
            fieldKey: _durationFieldKey,
            title: LocaleKeys.ownerAddPropertyMinimumRentalMonths,
            value: widget.rentalDurationController.text,
            validator: PropertyFormValidation.rentalDuration,
          ),
          FirstValidationErrorField(
            fieldKey: _unitFieldKey,
            title: LocaleKeys.ownerAddPropertyPricePeriod,
            value: widget.form.rentalUnitApiValue,
            validator: PropertyFormValidation.rentalUnit,
          ),
          if (widget.form.rentalInventory == null)
            FirstValidationErrorField(
              fieldKey: _amenitiesFieldKey,
              title: LocaleKeys.ownerAddPropertyAmenities,
              value: widget.form.amenityApiValues.join(', '),
              validator: (_) => widget.form.unsupportedAmenities.isEmpty
                  ? null
                  : _unsupportedAmenitiesError,
            ),
          FirstValidationErrorField(
            fieldKey: _suitableForFieldKey,
            title: LocaleKeys.ownerAddPropertySuitableFor,
            value: widget.form.suitableForApiValue,
            validator: (value) =>
                PropertyTenantType.fromValue(value ?? '') != null
                ? null
                : LocaleKeys.fillField,
          ),
          if (widget.form.rentalInventory == null)
            FirstValidationErrorField(
              fieldKey: _descriptionFieldKey,
              title: LocaleKeys.ownerAddPropertyDescriptionLabel,
              value: widget.descriptionController.text,
              validator: PropertyFormValidation.description,
            ),
          FirstValidationErrorField(
            fieldKey: _buildingYearFieldKey,
            title: LocaleKeys.tenantPropertyDetailsBuildingYear,
            value: widget.form.buildingYear,
            validator: PropertyFormValidation.buildingYear,
          ),
          FirstValidationErrorField(
            fieldKey: _depositFieldKey,
            title: LocaleKeys.ownerAddPropertyDeposit,
            value: widget.form.deposit,
            validator: (_) => widget.form.isDepositReady
                ? null
                : LocaleKeys.ownerAddPropertyDepositInvalid,
          ),
        ];
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
        for (final type in PropertyTenantType.values)
          'suitable_for:${type.value}':
              options.suitableFor
                  .where((option) => option.value == type.value)
                  .firstOrNull
                  ?.label ??
              type.label,
        for (final option in options.pricePeriods)
          'price_period:${option.value}': option.label,
        for (final period in PropertyPricePeriod.values)
          'price_period:${period.value}':
              options.pricePeriods
                  .where((option) => option.value == period.value)
                  .firstOrNull
                  ?.label ??
              period.label,
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
    if (widget.form.isPartialOffering) {
      return AddPropertyStepShell(
        validationFields: _validationFields,
        activeSegments: 3,
        segmentCount: 3,
        progressSubtitle: LocaleKeys.rentalOfferTerms,
        primaryLabel: widget.isSubmitting
            ? LocaleKeys.ownerAddPropertySubmitting
            : LocaleKeys.ownerPropertyReviewAction,
        onPrimaryTap: widget.isSubmitting ? null : widget.onNext,
        children: [
          PropertySelectionField(
            key: _priceFieldKey,
            isValid: widget.form.isPricingReady,
            message: LocaleKeys.rentalInvalidInventory,
            child: RentalOfferTermsEditor(
              inventory: widget.form.rentalInventory!,
              onChanged: (inventory) => widget.onAdditionalDetailsChanged(
                widget.form.copyWith(rentalInventory: inventory),
              ),
            ),
          ),
          if (!widget.form.canSaveToServer())
            AddPropertyInfoBanner(
              text: LocaleKeys.rentalLocalOnly,
              backgroundColor: context.appColor(
                AppColors.amberPale,
                surface: true,
              ),
            ),
        ],
      );
    }
    return AddPropertyStepShell(
      validationFields: _validationFields,
      activeSegments: 3,
      segmentCount: 3,
      progressSubtitle: LocaleKeys.ownerAddPropertyPricingProgress,
      primaryLabel: widget.isSubmitting
          ? LocaleKeys.ownerAddPropertySubmitting
          : LocaleKeys.ownerPropertyReviewAction,
      onPrimaryTap: !widget.isSubmitting ? widget.onNext : null,
      children: [
        _PriceSection(
          priceFieldKey: _priceFieldKey,
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
                  return Column(
                    spacing: 16,
                    children: [
                      AddPropertyRentalPeriodSection(
                        durationFieldKey: _durationFieldKey,
                        unitFieldKey: _unitFieldKey,
                        form: widget.form,
                        rentalDurationController:
                            widget.rentalDurationController,
                        onRentalDurationChanged: widget.onRentalDurationChanged,
                        onRentalUnitChanged: widget.onRentalUnitChanged,
                        options: [
                          for (final period in PropertyPricePeriod.values)
                            options.pricePeriods
                                    .where(
                                      (option) => option.value == period.value,
                                    )
                                    .firstOrNull ??
                                TenantFilterOption(
                                  value: period.value,
                                  label: period.label,
                                ),
                        ],
                      ),
                      if (widget.form.rentalInventory == null)
                        AddPropertySectionCard(
                          key: _amenitiesFieldKey,
                          title: LocaleKeys.ownerAddPropertyAmenities,
                          child: AddPropertyChipWrap(
                            chips: [
                              AddPropertyChipContent(
                                label: LocaleKeys.ownerAddPropertyFurnished,
                                value: 'furnished',
                                isSelected: widget.form.amenityApiValues
                                    .contains('furnished'),
                              ),
                              for (final option in options.amenities)
                                if (OwnerAddPropertyContent
                                    .supportedAmenityValues
                                    .contains(option.value))
                                  AddPropertyChipContent(
                                    label: option.label,
                                    value: option.value,
                                    isSelected: widget.form.amenityApiValues
                                        .contains(option.value),
                                  ),
                              for (final value in widget.form.amenityApiValues)
                                if (value != 'furnished' &&
                                    (!OwnerAddPropertyContent
                                            .supportedAmenityValues
                                            .contains(value) ||
                                        !options.amenities.any(
                                          (option) => option.value == value,
                                        )))
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
                        child: PropertySelectionField(
                          key: _suitableForFieldKey,
                          isValid:
                              PropertyTenantType.fromValue(
                                widget.form.suitableForApiValue,
                              ) !=
                              null,
                          child: AddPropertyChipWrap(
                            chips: [
                              for (final type in PropertyTenantType.values)
                                AddPropertyChipContent(
                                  label:
                                      options.suitableFor
                                          .where(
                                            (option) =>
                                                option.value == type.value,
                                          )
                                          .firstOrNull
                                          ?.label ??
                                      type.label,
                                  value: type.value,
                                  isSelected:
                                      widget.form.suitableForApiValue ==
                                      type.value,
                                ),
                            ],
                            onChipTap: (chip) => widget.onSuitableForSelected(
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
        if (widget.listingAssistant != null) widget.listingAssistant!,
        if (widget.form.rentalInventory == null)
          _DescriptionSection(
            descriptionFieldKey: _descriptionFieldKey,
            descriptionController: widget.descriptionController,
            onDescriptionChanged: widget.onDescriptionChanged,
          ),
        AddPropertyAdditionalDetails(
          buildingYearFieldKey: _buildingYearFieldKey,
          depositFieldKey: _depositFieldKey,
          form: widget.form,
          onDetailsChanged: widget.onAdditionalDetailsChanged,
        ),
        if (widget.form.unsupportedAmenities.isNotEmpty)
          AddPropertyInfoBanner(
            text: _unsupportedAmenitiesError,
            backgroundColor: context.appColor(
              AppColors.amberPale,
              surface: true,
            ),
            icon: Icons.info_outline_rounded,
          ),
        AddPropertyInfoBanner(
          text: widget.form.isPricingReady
              ? LocaleKeys.ownerAddPropertyPricingReady
              : LocaleKeys.ownerAddPropertyPricingRequired,
          backgroundColor: widget.form.isPricingReady
              ? context.appColor(AppColors.greenPale, surface: true)
              : context.appColor(AppColors.amberPale, surface: true),
          borderColor: widget.form.isPricingReady
              ? AppColors.greenAlpha19
              : AppColors.goldAlpha15,
          iconColor: widget.form.isPricingReady
              ? context.appColor(AppColors.green)
              : context.appColor(AppColors.brown),
          textColor: widget.form.isPricingReady
              ? context.appColor(AppColors.sokoonNavy)
              : context.appColor(AppColors.brown),
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
    required this.priceFieldKey,
  });

  final OwnerAddPropertyFormState form;
  final TextEditingController monthlyPriceController;
  final ValueChanged<String> onMonthlyPriceChanged;
  final GlobalKey priceFieldKey;

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: form.rentalInventory != null
          ? LocaleKeys.rentalEntirePriceBasis
          : LocaleKeys.ownerAddPropertyPrice,
      child: Column(
        spacing: 10.h,
        children: [
          AddPropertyField(
            key: priceFieldKey,
            field: AddPropertyFieldContent(
              label: LocaleKeys.ownerAddPropertyPrice,
              value: '0',
              isFocused: true,
              textAlign: TextAlign.start,
            ),
            validator: PropertyFormValidation.price,
            controller: monthlyPriceController,
            onChanged: onMonthlyPriceChanged,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [
              const LocalizedDigitsFormatter(allowDecimal: true),
            ],
            suffix: AppText(
              EgyptianPoundText.symbol,
              style: AppTextStyles.bold13.copyWith(
                color: context.appColor(AppColors.sokoonGray),
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

class _DescriptionSection extends StatelessWidget {
  const _DescriptionSection({
    required this.descriptionController,
    required this.onDescriptionChanged,
    required this.descriptionFieldKey,
  });

  final TextEditingController descriptionController;
  final ValueChanged<String> onDescriptionChanged;
  final GlobalKey descriptionFieldKey;

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyDescription,
      child: AddPropertyField(
        key: descriptionFieldKey,
        field: AddPropertyFieldContent(
          label: LocaleKeys.ownerAddPropertyDescriptionLabel,
          value: LocaleKeys.ownerAddPropertyDescriptionHint,
        ),
        validator: PropertyFormValidation.description,
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
