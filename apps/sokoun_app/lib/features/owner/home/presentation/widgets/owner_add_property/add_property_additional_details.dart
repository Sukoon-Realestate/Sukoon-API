import 'dart:io';

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';

import '../../../data/models/owner_add_property_content.dart';
import 'add_property_field.dart';
import 'add_property_section_card.dart';
import 'add_property_chip_wrap.dart';

class AddPropertyAdditionalDetails extends StatefulWidget {
  const AddPropertyAdditionalDetails({
    super.key,
    required this.form,
    required this.onDetailsChanged,
  });

  final OwnerAddPropertyFormState form;
  final ValueChanged<OwnerAddPropertyFormState> onDetailsChanged;

  @override
  State<AddPropertyAdditionalDetails> createState() =>
      _AddPropertyAdditionalDetailsState();
}

class _AddPropertyAdditionalDetailsState
    extends State<AddPropertyAdditionalDetails> {
  static const Set<String> _depositPresets = {
    'none',
    'half_month',
    'one_month',
    'two_months',
  };
  late final TextEditingController _country;
  late final TextEditingController _neighborhood;
  late final TextEditingController _buildingYear;
  late final TextEditingController _deposit;
  final ValueNotifier<bool> _isPickingProof = ValueNotifier(false);

  @override
  void initState() {
    super.initState();
    _country = TextEditingController(text: widget.form.country);
    _neighborhood = TextEditingController(text: widget.form.neighborhood);
    _buildingYear = TextEditingController(text: widget.form.buildingYear);
    _deposit = TextEditingController(
      text: _depositPresets.contains(widget.form.deposit)
          ? ''
          : widget.form.deposit,
    );
  }

  @override
  void didUpdateWidget(covariant AddPropertyAdditionalDetails oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_controllerValues.entries.every(
      (entry) => entry.key.text == entry.value,
    )) {
      return;
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      for (final entry in _controllerValues.entries) {
        if (entry.key.text != entry.value) {
          entry.key.value = TextEditingValue(
            text: entry.value,
            selection: TextSelection.collapsed(offset: entry.value.length),
          );
        }
      }
    });
  }

  Map<TextEditingController, String> get _controllerValues => {
    _country: widget.form.country,
    _neighborhood: widget.form.neighborhood,
    _buildingYear: widget.form.buildingYear,
    _deposit: _depositPresets.contains(widget.form.deposit)
        ? ''
        : widget.form.deposit,
  };

  @override
  void dispose() {
    _country.dispose();
    _neighborhood.dispose();
    _buildingYear.dispose();
    _deposit.dispose();
    _isPickingProof.dispose();
    super.dispose();
  }

  Future<void> _pickProof() async {
    if (_isPickingProof.value) return;
    _isPickingProof.value = true;
    try {
      final File? file = await Helpers.getImage();
      if (!mounted || file == null) return;
      widget.onDetailsChanged(
        widget.form.copyWith(
          ownershipProofFile: file,
          removeOwnershipProof: false,
        ),
      );
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: AppText(LocaleKeys.exceptionError)));
      }
    } finally {
      if (mounted) _isPickingProof.value = false;
    }
  }

  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: LocaleKeys.ownerAddPropertyAdditionalDetails,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 12,
      children: [
        AddPropertyField(
          field: AddPropertyFieldContent(
            label: LocaleKeys.ownerAddPropertyCountry,
            value: '',
          ),
          controller: _country,
          isRequired: false,
          onChanged: (value) =>
              widget.onDetailsChanged(widget.form.copyWith(country: value)),
        ),
        AddPropertyField(
          field: AddPropertyFieldContent(
            label: LocaleKeys.ownerAddPropertyNeighborhood,
            value: '',
          ),
          controller: _neighborhood,
          isRequired: false,
          onChanged: (value) => widget.onDetailsChanged(
            widget.form.copyWith(neighborhood: value),
          ),
        ),
        AddPropertyField(
          field: AddPropertyFieldContent(
            label: LocaleKeys.tenantPropertyDetailsBuildingYear,
            value: '',
          ),
          controller: _buildingYear,
          isRequired: false,
          keyboardType: TextInputType.number,
          inputFormatters: [const LocalizedDigitsFormatter()],
          validator: (value) {
            if (value == null || value.trim().isEmpty) return null;
            final int? year = int.tryParse(value);
            return year != null && year >= 1800 && year <= DateTime.now().year
                ? null
                : LocaleKeys.ownerAddPropertyBuildingYearInvalid;
          },
          onChanged: (value) => widget.onDetailsChanged(
            widget.form.copyWith(buildingYear: value),
          ),
        ),
        AppText(LocaleKeys.ownerAddPropertyDeposit),
        AddPropertyChipWrap(
          chips: [
            for (final entry in {
              'none': LocaleKeys.ownerAddPropertyNoDeposit,
              'half_month': LocaleKeys.ownerAddPropertyHalfMonth,
              'one_month': LocaleKeys.ownerAddPropertyOneMonth,
              'two_months': LocaleKeys.ownerAddPropertyTwoMonths,
              '': LocaleKeys.ownerAddPropertyCustomDeposit,
            }.entries)
              AddPropertyChipContent(
                label: entry.value,
                value: entry.key,
                isSelected: entry.key.isEmpty
                    ? !_depositPresets.contains(widget.form.deposit)
                    : widget.form.deposit == entry.key,
              ),
          ],
          onChipTap: (chip) => widget.onDetailsChanged(
            widget.form.copyWith(deposit: chip.value),
          ),
        ),
        if (!_depositPresets.contains(widget.form.deposit))
          AddPropertyField(
            field: AddPropertyFieldContent(
              label: LocaleKeys.ownerAddPropertyDeposit,
              value: '',
            ),
            controller: _deposit,
            hint: LocaleKeys.ownerAddPropertyDepositHint,
            isRequired: false,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            inputFormatters: [const LocalizedDigitsFormatter()],
            validator: (_) => widget.form.isDepositReady
                ? null
                : LocaleKeys.ownerAddPropertyDepositInvalid,
            onChanged: (value) =>
                widget.onDetailsChanged(widget.form.copyWith(deposit: value)),
          ),
        AppText(LocaleKeys.ownerAddPropertySmokingQuestion),
        AddPropertyChipWrap(
          chips: [
            AddPropertyChipContent(
              label: LocaleKeys.tenantPropertyDetailsSmokingAllowed,
              value: 'allowed',
              isSelected: widget.form.smokingAllowed == true,
            ),
            AddPropertyChipContent(
              label: LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
              value: 'not_allowed',
              isSelected: widget.form.smokingAllowed == false,
            ),
            AddPropertyChipContent(
              label: LocaleKeys.ownerAddPropertyNotSpecified,
              value: 'unspecified',
              isSelected: widget.form.smokingAllowed == null,
            ),
          ],
          onChipTap: (chip) => widget.onDetailsChanged(
            widget.form.copyWith(
              smokingAllowed: chip.value == 'allowed',
              clearSmokingAllowed: chip.value == 'unspecified',
            ),
          ),
        ),
        AppText(LocaleKeys.ownerAddPropertyProofTitle),
        AppText(
          LocaleKeys.ownerAddPropertyProofInternal,
          color: AppColors.sokoonGray,
        ),
        if (widget.form.hasOwnershipProof)
          AppText(LocaleKeys.ownerAddPropertyProofAttached),
        ValueListenableBuilder<bool>(
          valueListenable: _isPickingProof,
          builder: (context, isPicking, _) => Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: isPicking ? null : _pickProof,
                icon: const Icon(Icons.attach_file_rounded),
                label: AppText(
                  widget.form.hasOwnershipProof
                      ? LocaleKeys.ownerAddPropertyProofChange
                      : LocaleKeys.ownerAddPropertyProofUpload,
                ),
              ),
              if (widget.form.hasOwnershipProof)
                TextButton.icon(
                  onPressed: isPicking
                      ? null
                      : () => widget.onDetailsChanged(
                          widget.form.copyWith(
                            clearOwnershipProof: true,
                            removeOwnershipProof: true,
                          ),
                        ),
                  icon: const Icon(
                    Icons.delete_outline_rounded,
                    color: AppColors.red,
                  ),
                  label: AppText(
                    LocaleKeys.ownerPropertiesDelete,
                    color: AppColors.red,
                  ),
                ),
            ],
          ),
        ),
      ],
    ),
  );
}
