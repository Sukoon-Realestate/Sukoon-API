import 'package:equatable/equatable.dart';

class CurrentLocationArea extends Equatable {
  const CurrentLocationArea({required this.city, required this.district});

  final String city;
  final String district;

  String get searchQuery => [
    district.trim(),
    city.trim(),
  ].where((part) => part.isNotEmpty).toSet().join(' ');

  @override
  List<Object?> get props => [city, district];
}
