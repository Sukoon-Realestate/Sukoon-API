import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_accommodation_details.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/cubits/rental_inventory_mutation_cubit.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';

class OwnerRentalOffersPanel extends StatefulWidget {
  const OwnerRentalOffersPanel({
    super.key,
    required this.propertyId,
    required this.inventory,
    this.onConfirmed,
    this.onEditOffer,
    this.category = RentalListingCategory.all,
  });
  final String propertyId;
  final RentalInventory inventory;
  final ValueChanged<PropertyDetailsModel>? onConfirmed;
  final ValueChanged<String>? onEditOffer;
  final RentalListingCategory category;
  @override
  State<OwnerRentalOffersPanel> createState() => _OwnerRentalOffersPanelState();
}

class _OwnerRentalOffersPanelState extends State<OwnerRentalOffersPanel> {
  late final RentalInventoryMutationCubit _cubit =
      RentalInventoryMutationCubit();
  RentalInventory? _confirmed;
  void _confirm(PropertyDetailsModel property) {
    if (!mounted) return;
    _confirmed = property.rentalInventory;
    widget.onConfirmed?.call(property);
  }

  @override
  void didUpdateWidget(covariant OwnerRentalOffersPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.inventory != widget.inventory) _confirmed = null;
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      BlocBuilder<
        RentalInventoryMutationCubit,
        AsyncState<PropertyDetailsModel>
      >(
        bloc: _cubit,
        builder: (_, state) {
          final inventory = _confirmed ?? widget.inventory;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 8,
            children: [
              AppText(
                inventory.isPartial
                    ? LocaleKeys.rentalPartialMode
                    : inventory.isSupported
                    ? LocaleKeys.rentalEntireProperty
                    : LocaleKeys.rentalUnknownScope,
              ),
              AppText(LocaleKeys.rentalPublicationReview),
              for (final offer in inventory.offers.where(
                (offer) => widget.category.accepts(offer.scope),
              ))
                Card(
                  key: ValueKey(
                    offer.id.isNotEmpty ? offer.id : offer.draftKey,
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      spacing: 8,
                      children: [
                        AppText(
                          RentalOfferLabels.accommodation(
                            RentalSelection.fromOffer(
                              propertyId: widget.propertyId,
                              inventory: inventory,
                              offer: offer,
                            ),
                          ),
                        ),
                        AppText(
                          RentalOfferLabels.price(
                            RentalSelection.fromOffer(
                              propertyId: widget.propertyId,
                              inventory: inventory,
                              offer: offer,
                            ),
                          ),
                        ),
                        AppText(
                          RentalOfferLabels.availability(
                            offer.availability,
                            archived: offer.archived,
                          ),
                        ),
                        RentalAccommodationDetails(
                          inventory: inventory,
                          selection: RentalSelection.fromOffer(
                            propertyId: widget.propertyId,
                            inventory: inventory,
                            offer: offer,
                          ),
                        ),
                        if (offer.id.isNotEmpty)
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              TextButton(
                                onPressed: () => Go.to(
                                  PropertyDetailsScreen(
                                    propertyId: widget.propertyId,
                                    offerId: offer.id,
                                  ),
                                ),
                                child: AppText(LocaleKeys.freeOpenListing),
                              ),
                              if (widget.onEditOffer != null)
                                TextButton(
                                  onPressed: state.isLoading
                                      ? null
                                      : () => widget.onEditOffer!(offer.id),
                                  child: AppText(
                                    RentalOfferLabels.formTitle(
                                      offer.scope,
                                      editing: true,
                                    ),
                                  ),
                                ),
                            ],
                          ),
                        if (RentalOfferCapabilities
                                .configured
                                .canManageInventory &&
                            RentalOfferCapabilities.configured.canWrite &&
                            !offer.archived)
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              if (offer.canSetAvailability)
                                OutlinedButton(
                                  onPressed: state.isLoading
                                      ? null
                                      : () => _cubit.updateOffer(
                                          selection: RentalSelection.fromOffer(
                                            propertyId: widget.propertyId,
                                            inventory: inventory,
                                            offer: offer,
                                          ),
                                          availability: offer.isAvailable
                                              ? 'rented'
                                              : 'available',
                                          onSuccess: _confirm,
                                        ),
                                  child: AppText(
                                    offer.isAvailable
                                        ? LocaleKeys.rentalMarkRented
                                        : LocaleKeys.rentalMakeAvailable,
                                  ),
                                ),
                              if (offer.canArchive)
                                OutlinedButton(
                                  onPressed: state.isLoading
                                      ? null
                                      : () => _cubit.updateOffer(
                                          selection: RentalSelection.fromOffer(
                                            propertyId: widget.propertyId,
                                            inventory: inventory,
                                            offer: offer,
                                          ),
                                          archive: true,
                                          onSuccess: _confirm,
                                        ),
                                  child: AppText(LocaleKeys.rentalArchive),
                                ),
                            ],
                          ),
                      ],
                    ),
                  ),
                ),
              if (state.isLoading) const LinearProgressIndicator(),
              if (state.isError)
                AppText(state.msg ?? LocaleKeys.exceptionError),
            ],
          );
        },
      );
}
