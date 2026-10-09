import '../../../destinations/data/destination_resolver.dart';
import 'package:equatable/equatable.dart';

class RentalPropertyLink extends Equatable {
  const RentalPropertyLink({required this.propertyId, this.offerId});
  final String propertyId;
  final String? offerId;
  static RentalPropertyLink? parse(Uri uri) {
    final destination = DestinationResolver.propertyLink(uri);
    return destination == null
        ? null
        : RentalPropertyLink(
            propertyId: destination.id,
            offerId: destination.offerId,
          );
  }

  @override
  List<Object?> get props => [propertyId, offerId];
}
