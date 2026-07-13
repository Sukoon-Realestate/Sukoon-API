import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import '../cache_service.dart';

class UserTypeHelper {
  UserTypeHelper._();
  static UserTypeHelper? _instance;
  static UserTypeHelper get instance => _instance ??= UserTypeHelper._();

  final String _currentTypeKey = 'current_user_type';

  UserType get currentUserType {
    final String? userAsString = CacheStorage.read(_currentTypeKey);
    return userAsString.toUserType;
  }

  setUserType(UserType type) => CacheStorage.write(_currentTypeKey, type.name);
}
