import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';

import '../../data/account_access.dart';

/// Protects direct actions and rechecks verification before async results apply.
abstract class VerifiedActionCubit<T> extends AsyncCubit<T> {
  VerifiedActionCubit(super.initialData);

  bool checkVerification({void Function(String message)? onError}) {
    if (isClosed) return false;
    if (AccountAccess.isVerified) return true;
    final String message = LocaleKeys.accountVerificationRequired;
    setError(errorMessage: message);
    onError?.call(message);
    return false;
  }

  @override
  Future<void> executeAsyncWithBaseModel({
    required Future<Result<BaseModel<T>, Failure>> Function() operation,
    Function(BaseModel<T>)? onSuccess,
    Function(String message)? onError,
    bool withInternetInterceptor = false,
    bool showMsgOnSuccess = false,
    bool Function()? shouldApplyResult,
  }) async {
    if (!checkVerification(onError: onError)) return;
    await super.executeAsyncWithBaseModel(
      operation: () async {
        if (!AccountAccess.isVerified) {
          return Error(ServerFailure(LocaleKeys.accountVerificationRequired));
        }
        final result = await operation();
        return AccountAccess.isVerified
            ? result
            : Error(ServerFailure(LocaleKeys.accountVerificationRequired));
      },
      onSuccess: onSuccess,
      onError: onError,
      withInternetInterceptor: withInternetInterceptor,
      showMsgOnSuccess: showMsgOnSuccess,
      shouldApplyResult: shouldApplyResult,
    );
  }
}
