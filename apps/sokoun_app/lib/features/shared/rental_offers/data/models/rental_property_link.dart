import 'package:equatable/equatable.dart';

class RentalPropertyLink extends Equatable {
  const RentalPropertyLink({required this.propertyId, this.offerId});
  final String propertyId;
  final String? offerId;
  static RentalPropertyLink? parse(Uri uri) {
    if (uri.hasScheme &&
        (uri.scheme != 'https' ||
            !const {
              'sokoun.app',
              'www.sokoun.app',
            }.contains(uri.host.toLowerCase()))) {
      return null;
    }
    if (!uri.hasScheme && uri.hasAuthority) return null;
    final parts = uri.pathSegments;
    if (parts.length != 2 && parts.length != 4) return null;
    if (parts.first != 'properties' || parts[1].trim().isEmpty) return null;
    if (parts.length == 4 &&
        (parts[2] != 'offers' || parts[3].trim().isEmpty)) {
      return null;
    }
    final offer = parts.length == 4
        ? parts[3]
        : uri.queryParameters['offer_id'];
    return RentalPropertyLink(
      propertyId: parts[1],
      offerId: offer?.trim().isEmpty == true ? null : offer,
    );
  }

  @override
  List<Object?> get props => [propertyId, offerId];
}
