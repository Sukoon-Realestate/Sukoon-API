import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';

/// Account verification is independent of workspace and participant badges.
abstract final class AccountAccess {
  static bool get isVerified {
    if (injector.isRegistered<UserCubit>()) {
      final UserCubit cubit = UserCubit.instance;
      return cubit.isUserLoggedIn && cubit.user.isVerified;
    }
    final UserModel? user = UserModel.currentUser;
    return user != null &&
        user.id.isNotEmpty &&
        user.id != '0' &&
        user.isVerified;
  }

  static void requireVerification() {
    if (!isVerified) throw StateError(LocaleKeys.accountVerificationRequired);
  }
}
