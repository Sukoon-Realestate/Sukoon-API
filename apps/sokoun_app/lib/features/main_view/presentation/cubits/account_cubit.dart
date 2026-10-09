import 'dart:async';

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';

import '../../../shared/profile/data/models/account_content.dart';
import '../../../shared/profile/data/profile_json.dart';

/// The shared account response supplies identity, profile details and statistics.
class AccountCubit extends AsyncCubit<AccountContent> {
  AccountCubit() : super(const AccountContent.initial());

  Future<void>? _accountRequest;
  int? _requestGeneration;
  StreamSubscription<UserState>? _userSubscription;

  void restoreCachedProfile() {
    // Private profile responses stay in this account's live Cubit. The previous
    // convenience cache is deliberately not restored from unprotected storage.
  }

  Future<void> getAccount() {
    if (isClosed || !injector.isRegistered<UserCubit>()) {
      return Future<void>.value();
    }
    _watchUser();
    final int generation = AccountSession.generation;
    if (_requestGeneration == generation && _accountRequest != null) {
      return _accountRequest!;
    }
    _requestGeneration = generation;
    return _accountRequest = _loadAccount(generation).whenComplete(() {
      if (_requestGeneration == generation) _accountRequest = null;
    });
  }

  void _watchUser() {
    _userSubscription ??= UserCubit.instance.stream.listen((state) {
      if (state.userStatus == UserStatus.loggedIn) {
        if (state.userModel.id == data.user.id) updateFromUser(state.userModel);
      } else {
        updateData(const AccountContent.initial());
        reset();
      }
    });
  }

  Future<void> _loadAccount(int generation) async {
    final UserCubit userCubit = UserCubit.instance;
    if (!userCubit.isUserLoggedIn &&
        !await injector<NetworkService>().hasSessionCookies()) {
      return;
    }
    if (isClosed || generation != AccountSession.generation) return;

    AccountContent? loadedAccount;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<AccountContent>(
          api: ApiConstants.getAccData,
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          // Only an established identity may read its account cache.
          cacheKey: userCubit.isUserLoggedIn ? AccountContent.cacheKey : null,
          mapper: (json) {
            final AccountContent account = AccountContent.fromJson(
              profileJsonMap(json),
            );
            if (account.user.id.isEmpty || account.user.id == '0') {
              throw const FormatException('Missing authenticated account ID');
            }
            return account;
          },
          fromCacheJson: AccountContent.fromJson,
          toJson: (account) => account.toJson(),
        ),
      ),
      onSuccess: (response) => loadedAccount = response.data,
      withInternetInterceptor: true,
    );
    final AccountContent? account = loadedAccount;
    if (account == null ||
        isClosed ||
        generation != AccountSession.generation) {
      return;
    }
    await userCubit.setUserLoggedIn(user: account.identity);
  }

  void updateFromUser(UserModel user) {
    if (isClosed) return;
    final AccountContent updated = data.copyWith(
      user: data.user.copyWith(
        fullName: user.name,
        isVerified: user.isVerified,
      ),
      accountDetails: data.accountDetails.updateFromUser(user),
    );
    updateData(updated);
  }

  @override
  Future<void> close() => Future.wait<void>([
    super.close(),
    if (_userSubscription != null) _userSubscription!.cancel(),
  ]);
}
