part of 'user_cubit.dart';

mixin UserUtils {
  Future<void> _saveUser(UserModel user) async {
    logDebug('Account identity saved');
    await CacheStorage.write(_userKey, jsonEncode(user.toJson()));
  }
}
