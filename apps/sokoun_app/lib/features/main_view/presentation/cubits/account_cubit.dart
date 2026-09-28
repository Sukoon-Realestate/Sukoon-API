import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';

class AccountCubit extends AsyncCubit<UserModel> {
  AccountCubit() : super(UserModel.initial());

  Future<void> getAccount({
    void Function(TenantProfileContent profile)? onProfileLoaded,
  }) async {
    if (isClosed || !injector.isRegistered<UserCubit>()) return;
    final UserCubit userCubit = UserCubit.instance;
    final int generation = AccountSession.generation;
    if (!userCubit.isUserLoggedIn &&
        !await injector<NetworkService>().hasSessionCookies()) {
      return;
    }
    if (isClosed || generation != AccountSession.generation) return;

    UserModel? loadedUser;
    TenantProfileContent? loadedProfile;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call<UserModel>(
        CrudBaseParmas<UserModel>(
          api: ApiConstants.getAccData,
          httpRequestType: HttpRequestType.get,
          mapper: (json) {
            final Map<String, dynamic> account = Map<String, dynamic>.from(
              json as Map,
            );
            final UserModel user = UserModel.fromJson(account);
            if (user.id.isEmpty || user.id == '0') {
              throw const FormatException('Missing authenticated account ID');
            }
            loadedProfile = TenantProfileContent.fromJson(account);
            return user;
          },
        ),
      ),
      onSuccess: (response) => loadedUser = response.data,
      withInternetInterceptor: true,
    );

    final UserModel? user = loadedUser;
    if (user == null || isClosed || generation != AccountSession.generation) {
      return;
    }
    await userCubit.setUserLoggedIn(user: user);
    final TenantProfileContent? profile = loadedProfile;
    if (!isClosed && AccountSession.userId == user.id && profile != null) {
      onProfileLoaded?.call(profile);
    }
  }
}
