import 'package:equatable/equatable.dart';
import '../property_location_data.dart';
import 'property_location.dart';

class PropertyLocationState extends Equatable {
  const PropertyLocationState({
    this.selected,
    this.results = const [],
    this.failure,
  });
  const PropertyLocationState.initial()
    : selected = null,
      results = const [],
      failure = null;
  final PropertyLocation? selected;
  final List<PropertyLocation> results;
  final PropertyLocationFailure? failure;

  PropertyLocationState copyWith({
    PropertyLocation? selected,
    List<PropertyLocation>? results,
    PropertyLocationFailure? failure,
  }) => PropertyLocationState(
    selected: selected ?? this.selected,
    results: results ?? this.results,
    failure: failure,
  );

  @override
  List<Object?> get props => [selected, results, failure];
}
