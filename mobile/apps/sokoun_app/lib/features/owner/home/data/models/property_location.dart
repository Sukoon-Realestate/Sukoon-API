import 'package:equatable/equatable.dart';
import 'package:melos_core/core/helpers/validators.dart';

class PropertyLocation extends Equatable {
  const PropertyLocation({
    required this.latitude,
    required this.longitude,
    this.address = '',
  });

  const PropertyLocation.initial()
    : latitude = 30.0444,
      longitude = 31.2357,
      address = '';

  factory PropertyLocation.fromJson(Map<String, dynamic> json) =>
      PropertyLocation(
        latitude: double.tryParse('${json['latitude']}') ?? double.nan,
        longitude: double.tryParse('${json['longitude']}') ?? double.nan,
        address: json['address']?.toString() ?? '',
      );

  final double latitude;
  final double longitude;
  final String address;

  bool get isValid =>
      Validators.isValidCoordinates(latitude: latitude, longitude: longitude);
  String get coordinates =>
      '${latitude.toStringAsFixed(6)}, ${longitude.toStringAsFixed(6)}';

  PropertyLocation copyWith({
    double? latitude,
    double? longitude,
    String? address,
  }) => PropertyLocation(
    latitude: latitude ?? this.latitude,
    longitude: longitude ?? this.longitude,
    address: address ?? this.address,
  );

  Map<String, dynamic> toJson() => {
    'latitude': latitude,
    'longitude': longitude,
    'address': address,
  };

  @override
  List<Object?> get props => [latitude, longitude, address];
}
