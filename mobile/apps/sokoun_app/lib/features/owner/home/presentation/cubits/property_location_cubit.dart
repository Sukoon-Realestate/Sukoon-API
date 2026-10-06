import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import '../../data/models/property_location.dart';
import '../../data/models/property_location_state.dart';
import '../../data/property_location_data.dart';

class PropertyLocationCubit extends AsyncCubit<PropertyLocationState> {
  PropertyLocationCubit({PropertyLocationDataSource? source})
    : _source =
          source ??
          (injector.isRegistered<PropertyLocationDataSource>()
              ? injector<PropertyLocationDataSource>()
              : const NativePropertyLocationData()),
      super(const PropertyLocationState.initial());

  final PropertyLocationDataSource _source;
  int _generation = 0;

  void initialize(PropertyLocation? location) {
    if (location?.isValid == true) select(location!);
  }

  void select(PropertyLocation location) {
    if (isClosed || !location.isValid) return;
    final int generation = ++_generation;
    emit(
      state.copyWith(
        status: BaseStatus.success,
        data: data.copyWith(selected: location, results: const []),
      ),
    );
    _resolveAddress(location, generation);
  }

  Future<void> _resolveAddress(
    PropertyLocation location,
    int generation,
  ) async {
    try {
      final address = await _source.addressFor(location);
      if (isClosed || generation != _generation || address.isEmpty) return;
      updateData(data.copyWith(selected: location.copyWith(address: address)));
    } catch (_) {
      // Coordinates remain usable when the native geocoder is offline.
    }
  }

  void clearSearch() {
    if (isClosed) return;
    ++_generation;
    emit(
      state.copyWith(
        status: BaseStatus.success,
        data: data.copyWith(results: const []),
      ),
    );
  }

  Future<void> search(String query) async {
    if (isClosed) return;
    if (query.trim().isEmpty) return clearSearch();
    final int generation = ++_generation;
    updateData(data.copyWith(results: const []));
    setLoading();
    try {
      final results = await _source.search(query.trim());
      if (isClosed || generation != _generation) return;
      final firstLocation = results.firstOrNull;
      emit(
        state.copyWith(
          status: BaseStatus.success,
          data: data.copyWith(
            selected: firstLocation,
            results: results,
            failure: results.isEmpty ? PropertyLocationFailure.noResults : null,
          ),
        ),
      );
      if (firstLocation != null) {
        _resolveAddress(firstLocation, generation);
      }
    } catch (_) {
      _fail(PropertyLocationFailure.unavailable, generation);
    }
  }

  Future<void> locate() async {
    if (isClosed || isLoading) return;
    final int generation = ++_generation;
    updateData(data.copyWith(results: const []));
    setLoading();
    try {
      final location = await _source.currentLocation();
      if (!isClosed && generation == _generation) select(location);
    } catch (error) {
      _fail(
        error is PropertyLocationFailure
            ? error
            : PropertyLocationFailure.unavailable,
        generation,
      );
    }
  }

  void _fail(PropertyLocationFailure failure, int generation) {
    if (isClosed || generation != _generation) return;
    emit(
      state.copyWith(
        status: BaseStatus.success,
        data: data.copyWith(failure: failure),
      ),
    );
  }

  Future<void> openSettings() async {
    if (isClosed) return;
    final generation = _generation;
    try {
      final opened = await _source.openSettings(
        appSettings:
            data.failure == PropertyLocationFailure.permissionDeniedForever,
      );
      if (!opened) _fail(PropertyLocationFailure.unavailable, generation);
    } catch (_) {
      _fail(PropertyLocationFailure.unavailable, generation);
    }
  }

  @override
  Future<void> close() {
    ++_generation;
    return super.close();
  }
}
