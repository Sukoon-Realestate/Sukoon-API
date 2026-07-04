part of 'user_cubit.dart';

mixin UserUtils {
  Future<void> _saveUser(UserModel user) async {
    logDebug('user saved: ${user.toJson()}');
    await CacheStorage.write(
      _userKey,
      jsonEncode(user.toJson()),
    );
  }

  Future<void> _saveToken(String token) async {
    await SecureStorage.write(_tokenKey, token);
  }
}
