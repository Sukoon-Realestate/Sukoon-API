import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:multiple_result/multiple_result.dart';
import '../../../../../../config/language/locale_keys.g.dart';
import '../../../../../../config/res/config_imports.dart';
import '../../../../../error/failure.dart';
import '../../../../../extensions/object.dart';
import '../../../../../shared/base_state.dart';
import '../../../../../widgets/toast_messages/custom_messages.dart';
import '../../../../../widgets/toast_messages/toast_message.dart';
import '../../../domain/base_domain_imports.dart';
import '../../../domain/usecases/pagination_response.dart';
part 'async_state.dart';

abstract class AsyncCubit<T> extends Cubit<AsyncState<T>> {
  AsyncCubit(T initialData) : super(AsyncState.initial(data: initialData)) {
    baseCrudUseCase = injector();
  }
  late final BaseCrudUseCase baseCrudUseCase;

  T get data => state.data;
  void setLoading() {
    emit(state.loading());
  }

  void setLoadingMore() {
    emit(state.loadingMore());
  }

  void setSuccess(BaseModel<T> data) {
    emit(state.success(data: data.data, msg: data.msg));
    if (data.key == 'fromCache') {
      MessageUtils.showTopMsg(data.msg);
    }
  }

  void setError({String? errorMessage}) {
    emit(state.error(errorMessage: errorMessage));
  }

  void reset() {
    emit(AsyncState.initial(data: state.data));
  }

  void updateData(T data) {
    emit(state.copyWith(data: data));
  }

  void updateErrorMessage(String? errorMessage) {
    emit(state.copyWith(msg: errorMessage));
  }

  bool get isLoading => state.isLoading;

  StreamSubscription? _streamSubscription;
  Future<void> executeAsyncWithBaseModel({
    required Future<Result<BaseModel<T>, Failure>> Function() operation,
    Function(BaseModel<T>)? onSuccess,
    Function(String msg)? onError,
    bool withInternetInterceptor = false,
    bool showMsgOnSuccess = false,
  }) async {
    if (withInternetInterceptor) {
      await _basicOperationWithInternetInterceptor(
        operation: operation,
        successEmitter: onSuccess,
        onError: onError,
      );
    } else {
      await _basicOperation(
        operation: operation,
        successEmitter: onSuccess,
        onError: onError,
        showMsgOnSuccess: showMsgOnSuccess,
      );
    }
  }

  bool _firstRequest = true;
  FutureOr<void> _checkIsFirstTime(
    bool val, {
    required FutureOr<void> Function() onNotFirstTime,
  }) async {
    if (_firstRequest) {
      _firstRequest = false;
      return;
    } else {
      await onNotFirstTime.call();
    }
  }

  late final Connectivity _connectivity = Connectivity();
  Future<void> _basicOperationWithInternetInterceptor({
    required Future<Result<BaseModel<T>, Failure>> Function() operation,
    Function(BaseModel<T>)? successEmitter,
    Function(String msg)? onError,
    bool showMsgOnSuccess = false,
  }) async {
    await _basicOperation(
      operation: operation,
      successEmitter: successEmitter,
      onError: onError,
      showMsgOnSuccess: showMsgOnSuccess,
    );

    _streamSubscription = _connectivity.onConnectivityChanged.listen((
      status,
    ) async {
      if (status.contains(ConnectivityResult.none)) {
        if (state.data.isNull ||
            (state.data is List && (state.data as List).isEmpty)) {
          emit(state.error(errorMessage: LocaleKeys.checkInternet));
        } else {
          MessageUtils.showTopMsg(LocaleKeys.checkInternet);
        }
      } else {
        MessageUtils.showTopMsg(LocaleKeys.theInternetConnectionIsRestored);
        await _basicOperation(
          operation: operation,
          successEmitter: successEmitter,
          onError: onError,
          showMsgOnSuccess: showMsgOnSuccess,
        );
        // if(state.data.isNull || (state.data is List && (state.data as List).isEmpty)){
        //   await _basicOperation(
        //       operation: operation,
        //       successEmitter: successEmitter,
        //       onError: onError
        //   );
        // }
      }
      // _checkIsFirstTime(
      //     _firstRequest,
      //     onNotFirstTime: ()async{
      //       if(status.contains(ConnectivityResult.none)){
      //         if(state.data.isNull || (state.data is List && (state.data as List).isEmpty)){
      //           emit(state.error(errorMessage: LocaleKeys.checkInternet));
      //
      //         }else{
      //           MessageUtils.showSnackBar(LocaleKeys.checkInternet);
      //         }
      //
      //       }else{
      //         MessageUtils.showSnackBar(LocaleKeys.theInternetConnectionIsRestored);
      //         if(state.data.isNull || (state.data is List && (state.data as List).isEmpty)){
      //           await _basicOperation(
      //               operation: operation,
      //               successEmitter: successEmitter,
      //               onError: onError
      //           );
      //         }
      //       }
      //     }
      // );
    });
  }

  Future<void> _basicOperation({
    required Future<Result<BaseModel<T>, Failure>> Function() operation,
    required Function(BaseModel<T>)? successEmitter,
    required Function(String msg)? onError,
    bool showMsgOnSuccess = false,
  }) async {
    setLoading();
    final result = await operation();
    result.when(
      (success) {
        if (showMsgOnSuccess && success.msg.isNotEmpty) {
          Messages.showToast(msg: success.msg, status: BaseStatus.error);
        }
        setSuccess(success);
        successEmitter?.call(success);
      },
      (failure) {
        Messages.showToast(msg: failure.message, status: BaseStatus.error);
        setError(errorMessage: failure.message);
        onError?.call(failure.message);
      },
    );
  }

  @override
  Future<void> close() async {
    await _streamSubscription?.cancel();
    return super.close();
  }

  @override
  void emit(AsyncState<T> state) {
    if (isClosed) return;
    super.emit(state);
  }
}
