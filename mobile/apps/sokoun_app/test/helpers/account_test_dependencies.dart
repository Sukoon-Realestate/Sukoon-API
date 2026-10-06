import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';

Future<TestAccountCubit> registerAuthenticatedTestAccount({
  UserModel user = const UserModel(
    id: '1',
    name: 'Test account',
    phone: '',
    email: 'test@example.com',
  ),
}) async {
  final TestAccountCubit cubit = TestAccountCubit(user);
  injector.registerSingleton<UserCubit>(
    cubit,
    dispose: (value) => value.close(),
  );
  await CacheStorage.write('user', user.toJson());
  AccountSession.begin(user.id);
  return cubit;
}

class TestAccountCubit extends UserCubit {
  TestAccountCubit(UserModel user) {
    emit(UserState(userModel: user, userStatus: UserStatus.loggedIn));
  }

  void signOut() {
    AccountSession.end();
    emit(UserState.initial());
  }
}
