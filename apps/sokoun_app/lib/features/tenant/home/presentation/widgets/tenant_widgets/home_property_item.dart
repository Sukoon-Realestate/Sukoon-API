import 'package:flutter/material.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'tenant_property_card.dart';

class HomePropertyItem extends StatelessWidget {
  const HomePropertyItem({super.key, required this.property});
  final HomePropertyModel property;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: property.id.isEmpty
            ? null
            : () => Go.to(PropertyDetailsScreen(propertyId: property.id)),
        child: TenantPropertyCard(
          isSponsored: property.isSponsored,
          title: property.title,
          rating: property.rate >= 0 && property.rate <= 5
              ? property.rate.toStringAsFixed(1)
              : '—',
          area: [
            PropertyDetailsModel.propertyTypeLabelFor(property.propertyType),
            property.location,
            ...RentalOfferLabels.listingFacts(property.rentalSummary),
            RentalOfferLabels.propertyArea(
              property.area,
              hasOffers: property.hasRentalOffers,
            ),
          ].where((value) => value.isNotEmpty).join(' · '),
          price: RentalOfferLabels.listingPrice(
            property.rentalSummary,
            hasInventory: property.hasRentalOffers,
            legacyPrice: property.price,
            legacyPeriod: property.pricePeriod,
          ),
          icon: property.propertyType == 'villa'
              ? Icons.villa_outlined
              : Icons.apartment_outlined,
          imageCount: property.imagesCount,
          imageUrl: property.mainImage,
        ),
      ),
    );
  }
}
