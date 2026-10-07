import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_draft_editing.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'add_property_section_card.dart';

class RentalScopeSelector extends StatefulWidget {
  const RentalScopeSelector({
    super.key,
    required this.inventory,
    required this.onChanged,
    required this.onLegacy,
    this.selectedScope,
    this.onScopeSelected,
    this.selectedOfferPersisted = false,
    this.showLocalNotice = true,
  });
  final RentalInventory? inventory;
  final ValueChanged<RentalInventory> onChanged;
  final VoidCallback onLegacy;
  final RentalScope? selectedScope;
  final ValueChanged<RentalScope>? onScopeSelected;
  final bool selectedOfferPersisted, showLocalNotice;
  @override
  State<RentalScopeSelector> createState() => _RentalScopeSelectorState();
}

class _RentalScopeSelectorState extends State<RentalScopeSelector> {
  late final ValueNotifier<bool> _expanded = ValueNotifier(
    widget.inventory == null,
  );
  @override
  void didUpdateWidget(covariant RentalScopeSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedScope != widget.selectedScope ||
        oldWidget.inventory?.mode != widget.inventory?.mode) {
      _expanded.value = widget.inventory == null;
    }
  }

  @override
  void dispose() {
    _expanded.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AddPropertySectionCard(
    title: LocaleKeys.rentalOfferQuestion,
    child: ValueListenableBuilder<bool>(
      valueListenable: _expanded,
      builder: (_, expanded, _) {
        final scope =
            widget.selectedScope ?? widget.inventory?.offers.firstOrNull?.scope;
        final persisted =
            widget.inventory != null &&
            RentalDraftEditing.hasPersistedOffers(widget.inventory!);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 8,
          children: [
            if (scope != null)
              Wrap(
                spacing: 8,
                runSpacing: 8,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  AppText(scope.label, fontWeight: FontWeight.bold),
                  if (!widget.selectedOfferPersisted)
                    TextButton(
                      onPressed: () => _expanded.value = !expanded,
                      child: AppText(LocaleKeys.editData),
                    ),
                ],
              ),
            if (expanded) ...[
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final type in RentalScope.values)
                    ChoiceChip(
                      label: AppText(type.label),
                      selected: scope == type,
                      onSelected:
                          widget.selectedOfferPersisted ||
                              (persisted &&
                                  (type == RentalScope.entireProperty ||
                                      widget.inventory!.mode == 'whole'))
                          ? null
                          : (_) {
                              _expanded.value = false;
                              if (widget.onScopeSelected != null) {
                                widget.onScopeSelected!(type);
                              } else {
                                widget.onChanged(
                                  RentalDraftEditing.chooseScope(
                                    widget.inventory,
                                    type,
                                  ),
                                );
                              }
                            },
                    ),
                ],
              ),
              AppText(LocaleKeys.rentalModeChangeHelp),
            ],
            if (widget.selectedOfferPersisted)
              AppText(LocaleKeys.rentalPersistedScopeLocked),
            if (widget.showLocalNotice &&
                widget.inventory != null &&
                !RentalOfferCapabilities.configured.canWrite)
              AppText(LocaleKeys.rentalLocalOnly),
            if (widget.inventory == null)
              TextButton(
                onPressed: widget.onLegacy,
                child: AppText(LocaleKeys.rentalLegacyFlow),
              ),
          ],
        );
      },
    ),
  );
}
