import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/inactivity_notification_service.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_device_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'features/splash_screen.dart';
import 'package:toastification/toastification.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

class Sokoon extends StatefulWidget {
  const Sokoon({super.key});

  @override
  State<Sokoon> createState() => _SokoonState();
}

class _SokoonState extends State<Sokoon> with WidgetsBindingObserver {
  StreamSubscription<void>? _expiredSubscription;
  StreamSubscription<UserState>? _userSubscription;
  bool _hadSession = false;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (!injector.isRegistered<WorkspaceCubit>()) {
      injector.registerSingleton<WorkspaceCubit>(WorkspaceCubit());
    }
    _hadSession = UserCubit.instance.isUserLoggedIn;
    _expiredSubscription = AccountSession.expired.listen((_) async {
      await NotificationDeviceData.unregisterCurrentDevice();
      await UserCubit.instance.logout();
    });
    _userSubscription = UserCubit.instance.stream.listen((state) {
      final bool wasLoggedIn = _hadSession;
      _hadSession = state.userStatus == UserStatus.loggedIn;
      if (wasLoggedIn && !_hadSession) {
        ChatRealtimeService.instance.setActiveConversation(null);
        unawaited(ChatRealtimeService.instance.disconnect());
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
    WidgetsBinding.instance.removeObserver(this);
    unawaited(_expiredSubscription?.cancel());
    unawaited(_userSubscription?.cancel());
    super.dispose();
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
        return BlocProvider(
          create: (context) => injector<UserCubit>(),
          child: ToastificationWrapper(
            child: MaterialApp(
              debugShowCheckedModeBanner: false,
              title: ConstantManager.projectName,
              theme: SokounTheme.light,
              localizationsDelegates: context.localizationDelegates,
              supportedLocales: context.supportedLocales,
              locale: context.locale,
              navigatorKey: Go.navigatorKey,
              home: SplashScreen(),
              builder: (context, child) {
                return Overlay(
                  initialEntries: [OverlayEntry(builder: (context) => child!)],
                );
              },
              navigatorObservers: [AppNavigationObserver.instance],
            ),
          ),
        );
      },
    );
  }
}
