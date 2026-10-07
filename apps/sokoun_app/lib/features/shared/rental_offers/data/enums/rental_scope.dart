import 'package:melos_core/config/language/locale_keys.g.dart';

enum RentalScope {
  entireProperty('entire_property'),
  room('room'),
  roomGroup('room_group'),
  bed('bed');

  const RentalScope(this.value);
  final String value;

  static RentalScope? fromValue(String? value) =>
      values.where((scope) => scope.value == value).firstOrNull;

  String get label => switch (this) {
    entireProperty => LocaleKeys.rentalEntireProperty,
    room => LocaleKeys.rentalRoom,
    roomGroup => LocaleKeys.rentalRoomGroup,
    bed => LocaleKeys.rentalBed,
  };

  String get priceBasis => switch (this) {
    entireProperty => LocaleKeys.rentalEntirePriceBasis,
    room => LocaleKeys.rentalRoomPriceBasis,
    roomGroup => LocaleKeys.rentalGroupPriceBasis,
    bed => LocaleKeys.rentalBedPriceBasis,
  };
}
