import 'favorite_coordinator.dart';
import '../../data/models/favorite_target.dart';
import 'package:sokoun_app/features/tenant/home/data/public_property_cache.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class PropertyDetailsCubit extends AsyncCubit<PropertyDetailsModel> {
  PropertyDetailsCubit()
    : super(
        const PropertyDetailsModel.initial(),
        showCacheFallbackMessage: false,
      );
  Future<void>? _loadRequest;

  Future<void> getPropertyDetails(String id) =>
      _loadRequest ??= _load(id).whenComplete(() => _loadRequest = null);

  Future<void> refresh(String id) async {
    await _loadRequest;
    if (!isClosed) await getPropertyDetails(id);
  }

  Future<void> _load(String id) async {
    if (isClosed || isLoading) return;
    if (data.id != id) {
      final cached = ObjectBoxCacheService.read(
        'property_details_$id',
        policy: ReadCachePolicy.publicListing,
      );
      if (cached != null) {
        final saved = PropertyDetailsModel.fromJson(cached);
        if (saved.id == id) {
          setSuccess(BaseModel(key: 'fromCache', msg: '', data: saved));
        }
      }
    }
    final revisions = {
      for (final entry in FavoriteCoordinator.instance.state.entries)
        entry.key: entry.value.revision,
    };
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.propertyDetails(id),
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.publicListing,
          cacheKey: 'property_details_$id',
          mapper: (json) => PropertyDetailsModel.fromJson(json),
          fromCacheJson: PropertyDetailsModel.fromJson,
          toJson: (model) => PublicPropertyCache.sanitize(model.toJson()),
        ),
      ),
      onSuccess: (response) {
        if (response.key == 'fromCache') return;
        final property = response.data;
        final target = FavoriteTarget(property.id);
        FavoriteCoordinator.instance.reconcile(
          target,
          property.isSaved,
          revisions[target] ?? 0,
        );
        for (final offer in property.rentalInventory?.offers ?? const []) {
          final target = FavoriteTarget(property.id, offer.id);
          FavoriteCoordinator.instance.reconcile(
            target,
            offer.isSaved,
            revisions[target] ?? 0,
          );
        }
      },
      withInternetInterceptor: true,
      retainDataOnRefresh: data.id == id,
    );
  }
}
