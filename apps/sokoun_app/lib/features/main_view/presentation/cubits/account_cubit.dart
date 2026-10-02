import 'dart:async';

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';

import '../../../shared/profile/data/account_data.dart';
import '../../../shared/profile/data/models/account_content.dart';

/// The shared account response supplies identity, profile details and statistics.
class AccountCubit extends AsyncCubit<AccountContent> {
  AccountCubit() : super(const AccountContent.initial());

  Future<void>? _accountRequest;
  int? _requestGeneration;
  StreamSubscription<UserState>? _userSubscription;

  void restoreCachedProfile() {
    if (isClosed || !UserModel.isAuthenticated) return;
    final Map<String, dynamic>? cached = ObjectBoxCacheService.read(
      AccountContent.cacheKey,
    );
    if (cached == null) return;
    final AccountContent profile = AccountContent.fromJson(cached);
    if (profile.user.id == UserModel.currentUser?.id) {
      emit(state.success(data: profile));
    }
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
        AccountData.request(cacheProfile: userCubit.isUserLoggedIn),
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
    if (!isClosed && AccountSession.userId == account.user.id) {
      ObjectBoxCacheService.save(AccountContent.cacheKey, account.toJson());
    }
  }

  void updateFromUser(UserModel user) {
    if (isClosed) return;
    final AccountContent updated = data.copyWith(
      user: data.user.copyWith(fullName: user.name),
      accountDetails: data.accountDetails.updateFromUser(user),
    );
    updateData(updated);
    ObjectBoxCacheService.save(AccountContent.cacheKey, updated.toJson());
  }

  @override
  Future<void> close() => Future.wait<void>([
    super.close(),
    if (_userSubscription != null) _userSubscription!.cancel(),
  ]);
}
