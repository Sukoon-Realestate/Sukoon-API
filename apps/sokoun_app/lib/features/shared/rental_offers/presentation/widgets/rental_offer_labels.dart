import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import '../../data/enums/rental_scope.dart';
import '../../data/models/rental_listing_summary.dart';
import '../../data/models/rental_selection.dart';

abstract final class RentalOfferLabels {
  static String detailsHeading(RentalScope? scope) => switch (scope) {
    RentalScope.room => LocaleKeys.rentalRoomDetails,
    RentalScope.roomGroup => LocaleKeys.rentalRoomGroupDetails,
    RentalScope.bed => LocaleKeys.rentalBedDetails,
    RentalScope.entireProperty => LocaleKeys.rentalPropertyDetails,
    null => LocaleKeys.rentalUnknownScope,
  };
  static String formTitle(RentalScope? scope, {bool editing = false}) =>
      switch (scope) {
        RentalScope.room =>
          editing ? LocaleKeys.rentalEditRoom : LocaleKeys.rentalAddRoom,
        RentalScope.roomGroup =>
          editing
              ? LocaleKeys.rentalEditRoomGroup
              : LocaleKeys.rentalAddRoomGroup,
        RentalScope.bed =>
          editing ? LocaleKeys.rentalEditBed : LocaleKeys.rentalAddBed,
        _ =>
          editing
              ? LocaleKeys.ownerPropertiesEditTitle
              : LocaleKeys.ownerAddPropertyTitle,
      };
  static String bathroom(String value) => switch (value) {
    'private' => LocaleKeys.rentalPrivateBathroom,
    'shared' => LocaleKeys.rentalSharedBathroom,
    _ => LocaleKeys.rentalUnspecified,
  };
  static String propertyArea(num area, {required bool hasOffers}) => area <= 0
      ? ''
      : hasOffers
      ? '${LocaleKeys.rentalParentPropertyArea}: $area'
      : '$area ${LocaleKeys.tenantSearchResultsSquareMeters}';
  static List<String> snapshotFacts(RentalSelection selection) => [
    if (selection.capacity != null && selection.capacity! > 0)
      '${selection.scope == RentalScope.bed
          ? LocaleKeys.rentalParentRoomCapacity
          : selection.scope == RentalScope.roomGroup
          ? LocaleKeys.rentalGroupCapacity
          : LocaleKeys.rentalRoomCapacity}: ${selection.capacity}',
    if (selection.bathroomAccess.isNotEmpty)
      selection.bathroomAccess.map(bathroom).join(' · '),
  ];
  static List<String> listingFacts(
    RentalListingSummary? summary, {
    String contextScope = '',
  }) => summary == null
      ? const []
      : [
          ...summary.scopes
              .map(RentalScope.fromValue)
              .nonNulls
              .where(
                (scope) => contextScope.isEmpty || scope.value == contextScope,
              )
              .map((scope) => scope.label)
              .toSet(),
          ...summary.labels,
          if (summary.count > 0)
            LocaleKeys.rentalOfferCount.replaceAll(
              '{count}',
              '${summary.count}',
            ),
        ];
  static String accommodation(RentalSelection selection) => [
    selection.scope?.label ??
        (selection.scopeValue == null
            ? LocaleKeys.rentalSnapshotMissing
            : LocaleKeys.rentalUnknownScope),
    if (selection.name.isNotEmpty) selection.name,
    if (selection.roomNames.isNotEmpty) selection.roomNames.join('، '),
    if (selection.bedName.isNotEmpty) selection.bedName,
  ].join(' · ');
  static String price(RentalSelection selection) => [
    EgyptianPoundText.format(
      selection.terms.price,
      period: selection.terms.pricePeriod,
    ),
    if (selection.scope != null) selection.scope!.priceBasis,
  ].join(' — ');

  /// Saved collections describe their saved offers, not a discovery minimum
  /// that may include other accommodation or a different price period.
  static String savedListingPrice(
    List<RentalSelection> selections, {
    required bool hasInventory,
    required String legacyPrice,
    required String legacyPeriod,
  }) {
    if (!hasInventory) {
      return EgyptianPoundText.format(legacyPrice, period: legacyPeriod);
    }
    if (selections.length != 1) return LocaleKeys.rentalSelectForPrice;
    final selection = selections.single;
    if (selection.scope == null ||
        !selection.terms.hasValidPrice ||
        PropertyPricePeriod.fromValue(selection.terms.pricePeriod) == null) {
      return LocaleKeys.rentalSelectForPrice;
    }
    return price(selection);
  }

  static String availability(String? value, {bool archived = false}) => archived
      ? LocaleKeys.rentalArchived
      : switch (value) {
          'available' => LocaleKeys.rentalAvailable,
          'rented' => LocaleKeys.rentalRented,
          'unavailable' => LocaleKeys.rentalUnavailable,
          _ => LocaleKeys.rentalUnknownAvailability,
        };
  static String listingPrice(
    RentalListingSummary? summary, {
    required bool hasInventory,
    required String legacyPrice,
    required String legacyPeriod,
    String contextScope = '',
    String contextPricePeriod = '',
  }) {
    if (summary == null) {
      return hasInventory
          ? LocaleKeys.rentalSelectForPrice
          : EgyptianPoundText.format(legacyPrice, period: legacyPeriod);
    }
    if (!summary.hasConfirmedPrice ||
        (contextScope.isNotEmpty && summary.priceScope != contextScope) ||
        (contextPricePeriod.isNotEmpty &&
            summary.pricePeriod != contextPricePeriod)) {
      return LocaleKeys.rentalSelectForPrice;
    }
    final price = EgyptianPoundText.format(
      summary.price,
      period: summary.pricePeriod,
    );
    final label = summary.startingFrom
        ? LocaleKeys.rentalStartingFrom.replaceAll('{price}', price)
        : price;
    return '$label — ${RentalScope.fromValue(summary.priceScope)!.priceBasis}';
  }
}
