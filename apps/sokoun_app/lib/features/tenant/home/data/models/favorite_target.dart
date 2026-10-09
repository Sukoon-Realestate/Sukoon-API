import 'package:equatable/equatable.dart';

class FavoriteTarget extends Equatable {
  const FavoriteTarget(this.propertyId, [this.offerId]);
  final String propertyId;
  final String? offerId;
  @override
  List<Object?> get props => [propertyId, offerId];
}

class FavoriteState {
  const FavoriteState({
    required this.confirmed,
    required this.desired,
    this.revision = 0,
    this.busy = false,
    this.error = '',
  });
  final bool confirmed;
  final bool desired;
  final int revision;
  final bool busy;
  final String error;
}
