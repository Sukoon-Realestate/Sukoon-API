/// Proposed v1 contracts, not evidence of deployment. Release defaults are off.
/// Configure each operation only after its server contract has been verified.
class RentalOfferCapabilities {
  const RentalOfferCapabilities({
    this.contractVersion = 0,
    this.inventoryWrites = false,
    this.search = false,
    this.favorites = false,
    this.viewings = false,
    this.mediaAssociations = false,
    this.inventoryActions = false,
  });

  static const configured = RentalOfferCapabilities(
    contractVersion: int.fromEnvironment('RENTAL_OFFERS_API_VERSION'),
    inventoryWrites: bool.fromEnvironment('RENTAL_OFFERS_WRITES'),
    search: bool.fromEnvironment('RENTAL_OFFERS_SEARCH'),
    favorites: bool.fromEnvironment('RENTAL_OFFERS_FAVORITES'),
    viewings: bool.fromEnvironment('RENTAL_OFFERS_VIEWINGS'),
    mediaAssociations: bool.fromEnvironment('RENTAL_OFFERS_MEDIA'),
    inventoryActions: bool.fromEnvironment('RENTAL_OFFERS_ACTIONS'),
  );

  final int contractVersion;
  final bool inventoryWrites, search, favorites, viewings;
  final bool mediaAssociations, inventoryActions;
  bool get supportsV1 => contractVersion == 1;
  bool get canWrite => supportsV1 && inventoryWrites;
  bool get canSearch => supportsV1 && search;
  bool get canFavorite => supportsV1 && favorites;
  bool get canRequestViewing => supportsV1 && viewings;
  bool get canAssociateMedia => canWrite && mediaAssociations;
  bool get canManageInventory => canWrite && inventoryActions;
}
