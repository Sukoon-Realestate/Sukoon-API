import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_picker.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../cubits/lease_property_cubit.dart';

class LeaseRentalOfferSelector extends StatefulWidget {
  const LeaseRentalOfferSelector({
    super.key,
    required this.propertyId,
    required this.selection,
    required this.enabled,
    required this.onSelected,
    this.refreshGeneration = 0,
  });
  final String propertyId;
  final RentalSelection? selection;
  final bool enabled;
  final int refreshGeneration;
  final ValueChanged<RentalSelection?> onSelected;
  @override
  State<LeaseRentalOfferSelector> createState() =>
      _LeaseRentalOfferSelectorState();
}

class _LeaseRentalOfferSelectorState extends State<LeaseRentalOfferSelector> {
  late final LeasePropertyCubit _cubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _cubit = LeasePropertyCubit();
    _request = _cubit.load(widget.propertyId);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant LeaseRentalOfferSelector oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.refreshGeneration != oldWidget.refreshGeneration) {
      _cubit.load(widget.propertyId);
    }
  }

  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<LeasePropertyCubit, PropertyDetailsModel>(
        cubit: _cubit,
        request: _request,
        initialData: const PropertyDetailsModel.initial(),
        onRetry: () => _cubit.load(widget.propertyId),
        builder: (property) {
          final inventory = property.rentalInventory;
          if (property.id != widget.propertyId) {
            return AppText(LocaleKeys.paidInvalidResponse);
          }
          if (inventory == null) return const SizedBox.shrink();
          return RentalOfferPicker(
            propertyId: property.id,
            inventory: inventory,
            selectedId: widget.selection?.offerId,
            confirmedSelection: widget.selection,
            enabled: widget.enabled && !_cubit.isCached,
            onSelected: (id) {
              final offer = inventory.offerById(id);
              widget.onSelected(
                offer == null
                    ? null
                    : RentalSelection.fromOffer(
                        propertyId: property.id,
                        inventory: inventory,
                        offer: offer,
                      ),
              );
            },
          );
        },
      );
}
