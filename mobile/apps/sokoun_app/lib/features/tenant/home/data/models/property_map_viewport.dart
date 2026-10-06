import 'package:equatable/equatable.dart';
import 'property_details_model.dart';

class PropertyMapViewport extends Equatable {
  const PropertyMapViewport({
    required this.south,
    required this.north,
    required this.west,
    required this.east,
  });
  const PropertyMapViewport.initial()
    : south = -90,
      north = 90,
      west = -180,
      east = 180;
  factory PropertyMapViewport.fromJson(Map<String, dynamic> json) =>
      PropertyMapViewport(
        south: (json['south'] as num).toDouble(),
        north: (json['north'] as num).toDouble(),
        west: (json['west'] as num).toDouble(),
        east: (json['east'] as num).toDouble(),
      );
  final double south, north, west, east;
  bool contains(PropertyDetailsModel property) {
    final latitude = double.tryParse(property.latitude);
    final longitude = double.tryParse(property.longitude);
    if (latitude == null ||
        longitude == null ||
        !latitude.isFinite ||
        !longitude.isFinite ||
        latitude < -90 ||
        latitude > 90 ||
        longitude < -180 ||
        longitude > 180) {
      return false;
    }
    return latitude >= south &&
        latitude <= north &&
        (west <= east
            ? longitude >= west && longitude <= east
            : longitude >= west || longitude <= east);
  }

  Map<String, dynamic> toJson() => {
    'south': south,
    'north': north,
    'west': west,
    'east': east,
  };
  PropertyMapViewport copyWith({
    double? south,
    double? north,
    double? west,
    double? east,
  }) => PropertyMapViewport(
    south: south ?? this.south,
    north: north ?? this.north,
    west: west ?? this.west,
    east: east ?? this.east,
  );
  @override
  List<Object?> get props => [south, north, west, east];
}
