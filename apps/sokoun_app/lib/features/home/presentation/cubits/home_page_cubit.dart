import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/home/data/models/home_page_model.dart';

class HomePageCubit extends AsyncCubit<HomePageModel> {
  HomePageCubit() : super(HomePageModel.initial());

  Future<void> getHomePage() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<HomePageModel>(
          api: ApiConstants.homePage,
          httpRequestType: HttpRequestType.get,
          mapper: (json) => HomePageModel.fromJson(json),
        ),
      ),
    );
  }
}
