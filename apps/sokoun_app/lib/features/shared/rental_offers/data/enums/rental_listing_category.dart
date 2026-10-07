import 'rental_scope.dart';

/// Collection categories are independent of the physical property type.
/// Unspecified keeps historical records accessible without guessing a scope.
enum RentalListingCategory {
  all,
  entireProperty,
  room,
  roomGroup,
  bed,
  unspecified;

  RentalScope? get scope => switch (this) {
    entireProperty => RentalScope.entireProperty,
    room => RentalScope.room,
    roomGroup => RentalScope.roomGroup,
    bed => RentalScope.bed,
    _ => null,
  };

  static RentalListingCategory fromScope(String value) =>
      switch (RentalScope.fromValue(value)) {
        RentalScope.entireProperty => entireProperty,
        RentalScope.room => room,
        RentalScope.roomGroup => roomGroup,
        RentalScope.bed => bed,
        null => value.isEmpty ? all : unspecified,
      };

  bool accepts(RentalScope? value) => this == all || value == scope;

  bool acceptsScopes(Iterable<RentalScope?> values) {
    if (this == all) return true;
    return values.isEmpty ? this == unspecified : values.any(accepts);
  }
}
