import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/notification/inactivity_notification_service.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/features/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_book_visit_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_filter_screen.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_property_details_screen.dart';
import 'package:toastification/toastification.dart';
import 'features/auth/presentation/screens/kyc_upload_documents_screen.dart';
import 'features/home/data/models/tenant_search_result_content.dart';
import 'features/home/presentation/screens/tenant_search_results_screen.dart';
import 'features/splash_screen.dart';

class Sokoon extends StatefulWidget {
  const Sokoon({super.key});

  @override
  State<Sokoon> createState() => _SokoonState();
}

class _SokoonState extends State<Sokoon> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    InactivityNotificationService.scheduleInactivityReminder();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
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
      builder: (ctx, child) {
        return BlocProvider(
          create: (context) => injector<UserCubit>(),
          child: ToastificationWrapper(
            child: MaterialApp(
              debugShowCheckedModeBanner: false,
              title: ConstantManager.projectName,
              theme: ThemeData(fontFamily: ConstantManager.fontFamily),
              localizationsDelegates: context.localizationDelegates,
              supportedLocales: context.supportedLocales,
              locale: context.locale,
              navigatorKey: Go.navigatorKey,
              home: KycUploadDocumentsScreen(),
              // home: TenantBookVisitScreen(property: TenantPropertyDetailsContent.fromSearchResult(SearchResultContent(title: '', district: '', location: '', rooms: '', bathrooms: '', area: '', tags: [], price: '', monthlyPrice: 100, rentalTerm: '', tenantType: '', smokingPolicy: '', amenities: [], photoCount: 8, imageColor: Colors.white, imageColorEnd: Colors.black, isVerified: true, propertyType: ''))),
              // home: RoleSelectScreen(
              //   onContinue: (role) {
              //     if (role == UserType.tenant) {
              //       Go.to(const TenantKycFlowScreen());
              //     }
              //   },
              // ),
              // home: LoginScreen(onAppleSignIn: (){}, onFacebookSignIn: (){}, onGoogleSignIn: (){},),

              // builder: (context, child) {
              //   return Overlay(
              //     initialEntries: [
              //       OverlayEntry(builder: (context) => Stack(
              //         children: [
              //           child!,
              //           ZegoUIKitPrebuiltCallMiniOverlayPage(
              //               contextQuery: () => Go.context
              //           ),
              //         ],
              //       )),
              //     ],
              //   );
              // },
              // home: const ContactUsChatScreen(),
              // home: const ZegoUIKitPrebuiltCallMiniPopScope(child: SplashScreen()),
              navigatorObservers: [AppNavigationObserver.instance],
            ),
          ),
        );
      },
    );
  }
}
