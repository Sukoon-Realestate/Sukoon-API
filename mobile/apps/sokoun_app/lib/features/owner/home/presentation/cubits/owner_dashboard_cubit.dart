import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';

class OwnerDashboardCubit extends AsyncCubit<OwnerDashboardModel> {
  OwnerDashboardCubit() : super(const OwnerDashboardModel.initial());

  Future<void> getDashboard() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerDashboardModel>(
          api: ApiConstants.ownerDashboard,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'owner_dashboard',
          mapper: (json) => OwnerDashboardModel.fromJson(json),
          fromCacheJson: OwnerDashboardModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
