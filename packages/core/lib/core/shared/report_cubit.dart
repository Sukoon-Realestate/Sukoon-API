import 'dart:async';

import '../base_crud/code/domain/base_domain_imports.dart';
import '../base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import '../network/api_endpoints.dart';

class ReportCubit extends AsyncCubit{
  ReportCubit() : super(null);

  Future<void> report({
    required int id,
    required String report,
    FutureOr<void> Function()? onSuccess
  })async{
    await executeAsyncWithBaseModel(
        operation: () async => await baseCrudUseCase.call(
            CrudBaseParmas(
              api: ApiConstants.report,
              httpRequestType: HttpRequestType.post,
              body: {
                'reported_id' : id,
                'report' : report
              },
            )
        ),

        onSuccess: (data) => onSuccess?.call()
    );
  }
}