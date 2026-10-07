import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../data/models/rent_overview.dart';
import '../../data/rent_overview_data.dart';

class RentOverviewCubit extends AsyncCubit<RentOverview> {
  RentOverviewCubit() : super(const RentOverview.initial());
  bool _isCached = true;
  bool get isCached => _isCached;

  Future<void> load() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => RentOverviewData.get(AppWorkspace.tenant),
      withInternetInterceptor: true,
      onSuccess: (response) => _isCached = response.key == 'fromCache',
    );
  }
}
