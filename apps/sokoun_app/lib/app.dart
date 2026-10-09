import 'features/shared/rental_offers/presentation/rental_property_link_navigation.dart';
import 'features/shared/recovery/data/private_recovery_data.dart';
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/inactivity_notification_service.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_device_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'features/splash_screen.dart';
import 'package:toastification/toastification.dart';
import 'package:sokoun_app/shared_widgets/sokoun_themed_app.dart';
import 'features/shared/appearance/data/theme_preferences.dart';
import 'features/shared/appearance/presentation/cubits/theme_cubit.dart';
import 'package:melos_core/core/navigation/page_router/imports_page_router_builder.dart';
import 'features/main_view/presentation/verified_feature_routes.dart';

class Sokoon extends StatefulWidget {
  const Sokoon({super.key});

  @override
  State<Sokoon> createState() => _SokoonState();
}

class _SokoonState extends State<Sokoon> with WidgetsBindingObserver {
  late final ThemeCubit _themeCubit;
  StreamSubscription<void>? _expiredSubscription;
  StreamSubscription<UserState>? _userSubscription;
  bool _hadSession = false;
  void Function()? _removeSessionCleanup;
  @override
  void initState() {
    super.initState();
    PrivateRecoveryData.initialize();
    _removeSessionCleanup = AccountSession.registerCleanup((_) async {
      WorkspaceNavigation.clearPending();
      ChatRealtimeService.instance.setActiveConversation(null);
      await Future.wait([
        ChatRealtimeService.instance.disconnect(),
        NotificationDeviceData.stop(),
      ]);
    });
    PageRouterBuilder().pageDecorator = VerifiedFeatureRoutes.wrap;
    _themeCubit = ThemeCubit(initialMode: ThemePreferences.read());
    WidgetsBinding.instance.addObserver(this);
    RentalPropertyLinkNavigation.reset();
    final initialLink = Uri.tryParse(
      WidgetsBinding.instance.platformDispatcher.defaultRouteName,
    );
    if (initialLink != null) RentalPropertyLinkNavigation.receive(initialLink);
    if (!injector.isRegistered<WorkspaceCubit>()) {
      injector.registerSingleton<WorkspaceCubit>(WorkspaceCubit());
    }
    _hadSession = UserCubit.instance.isUserLoggedIn;
    _expiredSubscription = AccountSession.expired.listen((_) async {
      await Future.wait([
        NotificationDeviceData.stop(),
        UserCubit.instance.logout(),
      ]);
    });
    _userSubscription = UserCubit.instance.stream.listen((state) {
      final bool wasLoggedIn = _hadSession;
      _hadSession = state.userStatus == UserStatus.loggedIn;
      if (_hadSession && !state.userModel.isVerified) {
        ChatRealtimeService.instance.setActiveConversation(null);
        unawaited(ChatRealtimeService.instance.disconnect());
      }
      if (wasLoggedIn && !_hadSession) {
        ChatRealtimeService.instance.setActiveConversation(null);
        ChatRealtimeService.instance.disconnect();
        WorkspaceNavigation.clearPending();
        WorkspaceCubit.instance.reset();
        if (Go.navigatorKey.currentState != null) {
          Go.offAll(const WelcomeScreen());
        }
      }
    });
    InactivityNotificationService.scheduleInactivityReminder();
  }

  @override
  void dispose() {
    _removeSessionCleanup?.call();
    PageRouterBuilder().pageDecorator = null;
    WidgetsBinding.instance.removeObserver(this);
    _expiredSubscription?.cancel();
    _userSubscription?.cancel();
    _themeCubit.close();
    super.dispose();
  }

  @override
  Future<bool> didPushRouteInformation(
    RouteInformation routeInformation,
  ) async => RentalPropertyLinkNavigation.receive(routeInformation.uri);

  @override
  Future<bool> didPushRoute(String route) async {
    final uri = Uri.tryParse(route);
    return uri != null && RentalPropertyLinkNavigation.receive(uri);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      InactivityNotificationService.scheduleInactivityReminder();
    }
  }

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: Size(ScreenSizes.width, ScreenSizes.height),
      minTextAdapt: true,
      splitScreenMode: true,
      // Layouts adapt to their constraints; controls retain logical dimensions.
      enableScaleWH: () => false,
      enableScaleText: () => false,
      fontSizeResolver: (size, _) => size.toDouble(),
      builder: (ctx, child) {
        return MultiBlocProvider(
          providers: [
            BlocProvider(create: (context) => injector<UserCubit>()),
            BlocProvider.value(value: _themeCubit),
          ],
          child: ToastificationWrapper(
            child: SokounThemedApp(home: SplashScreen()),
          ),
        );
      },
    );
  }
}
