import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';

abstract class PremiumMutationCubit<T> extends AsyncCubit<T> {
  PremiumMutationCubit(super.initialData);
  Future<T?> perform(
    Future<Result<BaseModel<T>, Failure>> Function() operation,
  ) async {
    if (isClosed || isLoading) return null;
    T? saved;
    await executeAsyncWithBaseModel(
      operation: operation,
      withInternetInterceptor: true,
      onSuccess: (response) => saved = response.data,
    );
    return isClosed ? null : saved;
  }
}
