import 'package:multiple_result/multiple_result.dart';

import '../error/failure.dart';

abstract class UseCase<T, Param> {
  Future<Result<T, Failure>> call(Param param);
  // i use [] to make param optional
}

abstract class UseCaseWithoutParam<T> {
  Future<Result<T, Failure>> call();
  // i use [] to make param optional
}
