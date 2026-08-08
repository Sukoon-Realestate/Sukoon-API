import 'dart:convert';
import 'dart:developer';
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../config/res/config_imports.dart';
import '../../helpers/apps_flyer/apps_flyer_helper.dart';
import '../../helpers/cache_service.dart';
import '../../helpers/nsfw_detector.dart';
import '../../local_db/objectbox_cache_service.dart';
import '../../network/interceptors/log_interceptor.dart';
import '../../network/network_service.dart';
import '../models/user_models/user_model.dart';
part 'user_state.dart';
part 'user_utils.dart';

const String _userKey = 'user';
const String _legacyTokenKey = 'token';

class UserCubit extends Cubit<UserState> with UserUtils {
  UserCubit() : super(UserState.initial());

  Future<void> setUserLoggedIn({required UserModel user}) async {
    await Future.wait([_saveUser(user), SecureStorage.delete(_legacyTokenKey)]);
    AppyFlyerHelper.setCustomer();
    emit(state.copyWith(userModel: user, userStatus: UserStatus.loggedIn));
  }

  Future<void> logout() async {
    try {
      await injector<NetworkService>().clearSessionCookies();
    } finally {
      await Future.wait([
        CacheStorage.delete(_userKey),
        SecureStorage.delete(_legacyTokenKey),
      ]);
      ObjectBoxCacheService.clearAll();
      NsfwDetectorHelper.terminate();
      emit(UserState.initial());
    }
  }

  Future<void> updateUser(UserModel user) async {
    await _saveUser(user);
    emit(state.copyWith(userModel: user));
  }

  Future<bool> init() async {
    final Map<String, dynamic>? userMap = CacheStorage.read(
      _userKey,
      isDecoded: true,
    );
    await SecureStorage.delete(_legacyTokenKey);
    final bool hasSessionCookies = await injector<NetworkService>()
        .hasSessionCookies();
    log(
      'Cached user exists: ${userMap != null}, '
      'cookie session exists: $hasSessionCookies',
    );
    if (hasSessionCookies && userMap != null) {
      AppyFlyerHelper.setCustomer();
      emit(
        state.copyWith(
          userModel: UserModel.fromJson(userMap),
          userStatus: UserStatus.loggedIn,
        ),
      );
      return true;
    }
    if (userMap != null) {
      await CacheStorage.delete(_userKey);
    }
    return false;
  }

  UserModel get user => state.userModel;
  static UserCubit get instance => injector<UserCubit>();

  bool get isUserLoggedIn => state.userStatus == UserStatus.loggedIn;
}
