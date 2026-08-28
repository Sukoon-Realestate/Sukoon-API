import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

class BookVisitCubit extends AsyncCubit<Map<String, dynamic>> {
  BookVisitCubit() : super({});

  Future<void> bookVisit({
    required String propertyId,
    required String visitDate,
    required String visitTime,
    required String note,
    required void Function() onSuccess,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: '${ApiConstants.properties}$propertyId/${ApiConstants.visits}',
          httpRequestType: HttpRequestType.post,
          body: {
            'visit_date': visitDate,
            'visit_time': visitTime,
            'note': note,
          },
          mapper: (json) =>
              json is Map<String, dynamic> ? json : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) => onSuccess(),
    );
  }
}
