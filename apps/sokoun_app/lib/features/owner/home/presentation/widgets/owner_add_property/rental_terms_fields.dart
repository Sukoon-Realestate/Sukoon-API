import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_tenant_type.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_terms.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'property_form_validation.dart';

class RentalTermsFields extends StatelessWidget {
  const RentalTermsFields({
    super.key,
    required this.terms,
    required this.fieldId,
    required this.onChanged,
    this.defaults = false,
    this.showDescription = true,
    this.inherited = const {},
    this.onInheritanceChanged,
  });
  final RentalTerms terms;
  final String fieldId;
  final ValueChanged<RentalTerms> onChanged;
  final bool defaults;
  final bool showDescription;
  final Set<String> inherited;
  final ValueChanged<Set<String>>? onInheritanceChanged;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 12,
    children: [
      if (!defaults) ...[
        RentalDraftField(
          fieldId: '$fieldId:price',
          label: '${LocaleKeys.ownerAddPropertyPrice} *',
          value: terms.price,
          numeric: true,
          validator: PropertyFormValidation.price,
          onChanged: (v) => onChanged(terms.copyWith(price: v)),
        ),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (final period in PropertyPricePeriod.values)
              ChoiceChip(
                label: AppText(period.label),
                selected: terms.pricePeriod == period.value,
                onSelected: (_) =>
                    onChanged(terms.copyWith(pricePeriod: period.value)),
              ),
          ],
        ),
        AppText(LocaleKeys.ownerAddPropertyPricePeriod),
      ],
      for (final field in RentalTerms.inheritedFields.where(
        (field) => showDescription || field != 'description',
      )) ...[
        if (!defaults)
          Material(
            type: MaterialType.transparency,
            child: CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: AppText(
                '${_label(field)} · ${LocaleKeys.rentalInherited}',
              ),
              value: inherited.contains(field),
              onChanged: (value) => onInheritanceChanged?.call(
                {...inherited}
                  ..remove(field)
                  ..addAll(value == true ? [field] : []),
              ),
            ),
          ),
        if (!inherited.contains(field))
          switch (field) {
            'rental_period' => RentalDraftField(
              fieldId: '$fieldId:$field',
              label: defaults ? _label(field) : '${_label(field)} *',
              value: terms.minimumMonths == 0 ? '' : '${terms.minimumMonths}',
              numeric: true,
              integer: true,
              validator: defaults
                  ? null
                  : PropertyFormValidation.rentalDuration,
              onChanged: (v) => onChanged(
                terms.copyWith(minimumMonths: int.tryParse(v) ?? 0),
              ),
            ),
            'deposit' => RentalDraftField(
              fieldId: '$fieldId:$field',
              label: _label(field),
              value: terms.deposit,
              onChanged: (v) => onChanged(terms.copyWith(deposit: v)),
            ),
            'description' => RentalDraftField(
              fieldId: '$fieldId:$field',
              label: _label(field),
              value: terms.description,
              multiline: true,
              onChanged: (v) => onChanged(terms.copyWith(description: v)),
            ),
            'rules' => RentalDraftField(
              fieldId: '$fieldId:$field',
              label: _label(field),
              value: terms.rules.join('\n'),
              multiline: true,
              onChanged: (v) => onChanged(
                terms.copyWith(
                  rules: v
                      .split('\n')
                      .where((r) => r.trim().isNotEmpty)
                      .toList(),
                ),
              ),
            ),
            'suitable_for' => Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final type in PropertyTenantType.values)
                  ChoiceChip(
                    label: AppText(type.label),
                    selected: terms.suitableFor == type.value,
                    onSelected: (_) =>
                        onChanged(terms.copyWith(suitableFor: type.value)),
                  ),
              ],
            ),
            _ => DropdownButtonFormField<String>(
              initialValue: terms.smokingAllowed == null
                  ? 'unknown'
                  : '${terms.smokingAllowed}',
              decoration: InputDecoration(labelText: _label(field)),
              items: [
                DropdownMenuItem(
                  value: 'unknown',
                  child: AppText(LocaleKeys.rentalUnspecified),
                ),
                DropdownMenuItem(
                  value: 'true',
                  child: AppText(
                    LocaleKeys.tenantPropertyDetailsSmokingAllowed,
                  ),
                ),
                DropdownMenuItem(
                  value: 'false',
                  child: AppText(
                    LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
                  ),
                ),
              ],
              isExpanded: true,
              onChanged: (v) => onChanged(
                terms.copyWith(
                  smokingAllowed: v == 'true',
                  clearSmoking: v == 'unknown',
                ),
              ),
            ),
          },
      ],
    ],
  );

  static String _label(String field) => switch (field) {
    'rental_period' => LocaleKeys.ownerAddPropertyMinimumRentalMonths,
    'deposit' => LocaleKeys.rentalOfferDeposit,
    'description' => LocaleKeys.rentalOfferDescription,
    'suitable_for' => LocaleKeys.rentalOfferSuitability,
    'rules' => LocaleKeys.rentalRules,
    _ => LocaleKeys.ownerAddPropertySmokingQuestion,
  };
}

/// Each field owns its controller and survives sibling and layout changes.
class RentalDraftField extends StatefulWidget {
  const RentalDraftField({
    super.key,
    required this.fieldId,
    required this.label,
    required this.value,
    required this.onChanged,
    this.numeric = false,
    this.multiline = false,
    this.integer = false,
    this.helperText,
    this.validator,
  });
  final String fieldId, label, value;
  final ValueChanged<String> onChanged;
  final bool numeric, multiline, integer;
  final String? helperText;
  final FormFieldValidator<String>? validator;
  @override
  State<RentalDraftField> createState() => _RentalDraftFieldState();
}

class _RentalDraftFieldState extends State<RentalDraftField> {
  late final TextEditingController _controller = TextEditingController(
    text: widget.value,
  );
  final FocusNode _focusNode = FocusNode();
  @override
  void didUpdateWidget(covariant RentalDraftField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_controller.text == widget.value ||
        (oldWidget.fieldId == widget.fieldId && _focusNode.hasFocus)) {
      return;
    }
    // A TextFormField notifies its ancestor Form when its controller changes.
    // Restored/externally edited values therefore sync after this build.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || _focusNode.hasFocus || _controller.text == widget.value) {
        return;
      }
      _controller.value = TextEditingValue(
        text: widget.value,
        selection: TextSelection.collapsed(offset: widget.value.length),
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 8,
    children: [
      // Floating input labels truncate at large text scales. Keep the complete
      // accommodation label outside the field and name the input for readers.
      AppText(widget.label),
      Semantics(
        label: widget.label,
        child: TextFormField(
          key: ValueKey(widget.fieldId),
          controller: _controller,
          focusNode: _focusNode,
          decoration: InputDecoration(
            helperText: widget.helperText,
            helperMaxLines: 12,
            errorMaxLines: 6,
          ),
          validator: widget.validator,
          keyboardType: widget.numeric
              ? TextInputType.numberWithOptions(decimal: !widget.integer)
              : widget.multiline
              ? TextInputType.multiline
              : TextInputType.text,
          inputFormatters: widget.numeric
              ? [LocalizedDigitsFormatter(allowDecimal: !widget.integer)]
              : null,
          minLines: widget.multiline ? 3 : 1,
          maxLines: widget.multiline ? 5 : 1,
          onChanged: widget.onChanged,
        ),
      ),
    ],
  );
}
