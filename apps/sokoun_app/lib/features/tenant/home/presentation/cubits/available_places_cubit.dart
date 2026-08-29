import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';

class AvailablePlacesCubit extends AsyncCubit<AvailablePlacesModel> {
  AvailablePlacesCubit() : super(const AvailablePlacesModel.initial());

  Future<void> getAvailablePlaces(String propertyTypeId) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<AvailablePlacesModel>(
          api: ApiConstants.availablePlaces,
          httpRequestType: HttpRequestType.get,
          queryParameters: {'property_type_id': propertyTypeId},
          mapper: (json) => AvailablePlacesModel.fromJson(json),
        ),
      ),
    );
  }
}
