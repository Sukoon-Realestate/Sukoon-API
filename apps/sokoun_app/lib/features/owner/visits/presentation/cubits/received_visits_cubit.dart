import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

class ReceivedVisitsCubit
    extends VerifiedActionCubit<List<OwnerVisitRequestContent>> {
  ReceivedVisitsCubit({this.requests = false}) : super(const []);
  final bool requests;

  Future<void> getReceivedVisits() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<List<OwnerVisitRequestContent>>(
          api: requests
              ? ApiConstants.ownerVisitRequests
              : ApiConstants.receivedPropertyVisits,
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheKey: requests ? 'owner_visit_requests' : 'owner_received_visits',
          mapper: OwnerVisitRequestContent.listFromResponse,
          fromCacheJson: OwnerVisitRequestContent.listFromResponse,
          toJson: (requests) => {
            'items': requests
                .map((request) => request.toJson())
                .toList(growable: false),
          },
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
