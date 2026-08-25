import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/visits/imports.dart';

class ReceivedVisitsCubit extends AsyncCubit<List<OwnerVisitRequestContent>> {
  ReceivedVisitsCubit() : super(const []);

  Future<void> getReceivedVisits() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<List<OwnerVisitRequestContent>>(
          api: ApiConstants.receivedPropertyVisits,
          httpRequestType: HttpRequestType.get,
          mapper: OwnerVisitRequestContent.listFromResponse,
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  void replaceRequest(OwnerVisitRequestContent request) {
    final List<OwnerVisitRequestContent> requests = List.of(data);
    final int index = requests.indexWhere((item) => item.id == request.id);
    if (index < 0) {
      return;
    }
    requests[index] = request;
    updateData(requests);
  }
}
