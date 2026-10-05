import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';

import 'add_property_field.dart';
import 'add_property_section_card.dart';
import 'property_form_validation.dart';

class AddPropertyRentalPeriodSection extends StatelessWidget {
  const AddPropertyRentalPeriodSection({
    super.key,
    required this.form,
    required this.rentalDurationController,
    required this.onRentalDurationChanged,
    required this.onRentalUnitChanged,
    required this.options,
    required this.durationFieldKey,
    required this.unitFieldKey,
  });

  final OwnerAddPropertyFormState form;
  final List<TenantFilterOption> options;
  final TextEditingController rentalDurationController;
  final ValueChanged<String> onRentalDurationChanged;
  final ValueChanged<String> onRentalUnitChanged;
  final GlobalKey durationFieldKey;
  final GlobalKey unitFieldKey;

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
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 6.h,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 10.w,
                children: [
                  Expanded(
                    flex: 4,
                    child: AddPropertyFieldLabel(
                      label: LocaleKeys.ownerAddPropertyMinimumRentalMonths,
                    ),
                  ),
                  Expanded(
                    flex: 6,
                    child: AddPropertyFieldLabel(
                      label: LocaleKeys.ownerAddPropertyPricePeriod,
                    ),
                  ),
                ],
              ),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 10.w,
                children: [
                  Expanded(
                    flex: 4,
                    child: Semantics(
                      label: LocaleKeys.ownerAddPropertyMinimumRentalMonths,
                      child: AddPropertyField(
                        key: durationFieldKey,
                        showLabel: false,
                        field: AddPropertyFieldContent(
                          label: LocaleKeys.ownerAddPropertyMinimumRentalMonths,
                          value: '0',
                          isFocused: true,
                          textAlign: TextAlign.center,
                        ),
                        validator: PropertyFormValidation.rentalDuration,
                        controller: rentalDurationController,
                        onChanged: onRentalDurationChanged,
                        keyboardType: TextInputType.number,
                        inputFormatters: [const LocalizedDigitsFormatter()],
                      ),
                    ),
                  ),
                  Expanded(
                    flex: 6,
                    child: Semantics(
                      label: LocaleKeys.ownerAddPropertyPricePeriod,
                      child: DropdownButtonFormField<TenantFilterOption>(
                        key: unitFieldKey,
                        isExpanded: true,
                        itemHeight: null,
                        validator: (_) => PropertyFormValidation.rentalUnit(
                          form.rentalUnitApiValue,
                        ),
                        decoration: InputDecoration(
                          errorMaxLines: 3,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 10.w,
                            vertical: 14.h,
                          ),
                        ),
                        hint: AppText(LocaleKeys.ownerAddPropertyChoose),
                        initialValue: selected,
                        selectedItemBuilder: (context) => [
                          for (final option in options)
                            Align(
                              alignment: AlignmentDirectional.centerStart,
                              child: AppText(
                                option.label,
                                style: AppTextStyles.medium.copyWith(
                                  fontSize: 14.sp,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                        ],
                        items: [
                          for (final option in options)
                            DropdownMenuItem(
                              value: option,
                              child: AppText(
                                option.label,
                                style: AppTextStyles.medium.copyWith(
                                  fontSize: 14.sp,
                                ),
                              ),
                            ),
                        ],
                        onChanged: (option) {
                          if (option != null) onRentalUnitChanged(option.value);
                        },
                      ),
                    ),
                  ),
                ],
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
              LocaleKeys.ownerAddPropertyRentalSummary.replaceAll(
                '{count}',
                form.rentalDuration,
              ),
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
