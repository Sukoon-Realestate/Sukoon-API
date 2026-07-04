import 'dart:async';

import '../base_crud/code/domain/base_domain_imports.dart';
import '../base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import '../network/api_endpoints.dart';

class BlockUserCubit extends AsyncCubit{
  BlockUserCubit() : super(null);

  Future<void> block({
    required int id,
    required void Function(String msg) onSuccess
  })async{
    await executeAsyncWithBaseModel(
        operation: () async => await baseCrudUseCase.call(
            CrudBaseParmas(
                api: ApiConstants.blockUser,
                httpRequestType: HttpRequestType.post,
                body: {'blocked_id' : id},
            )
        ),

      onSuccess: (data) => onSuccess.call(data.msg)
    );
  }
}