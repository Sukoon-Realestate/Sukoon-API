import 'package:injectable/injectable.dart';

import '../../../config/res/config_imports.dart';
import '../../network/dio_service.dart';
import '../../network/network_service.dart';
import '../../network/session_auth_service.dart';
import '../../notification/notification_service.dart';
import '../user_cubit/user_cubit.dart' show UserCubit;
import 'setup_service_locators.config.dart';

@InjectableInit(
  initializerName: 'init',
  preferRelativeImports: true,
  asExtension: true,
)
void setUpServiceLocator() {
  injector.init();
  setUpGeneralDependencies();
}

void setUpGeneralDependencies() {
  injector.registerLazySingleton<UserCubit>(() => UserCubit());

  injector.registerLazySingleton<NotificationService>(
    () => NotificationService(),
  );

  injector.registerLazySingleton<DioService>(DioService.new);
  injector.registerLazySingleton<NetworkService>(() => injector<DioService>());
  injector.registerLazySingleton<SessionAuthService>(
    () => injector<DioService>(),
  );
}
