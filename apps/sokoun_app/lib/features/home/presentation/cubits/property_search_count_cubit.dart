import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/home/data/models/property_search_model.dart';

class PropertySearchCountCubit extends AsyncCubit<int> {
  PropertySearchCountCubit() : super(0);

  int _requestSequence = 0;

  Future<void> getCount(PropertySearchFilters filters) async {
    final int requestSequence = ++_requestSequence;
    setLoading();

    final result = await baseCrudUseCase.call(
      CrudBaseParmas<int>(
        api: ApiConstants.properties,
        httpRequestType: HttpRequestType.get,
        queryParameters: filters
            .copyWith(page: 1, pageSize: 1)
            .toQueryParameters(),
        mapper: (json) => (json['count'] as num?)?.toInt() ?? 0,
      ),
    );

    if (requestSequence != _requestSequence || isClosed) return;

    result.when(
      setSuccess,
      (failure) => setError(errorMessage: failure.message),
    );
  }
}
