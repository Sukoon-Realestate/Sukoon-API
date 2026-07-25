import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:sokoun_app/features/chat/data/models/tenant_chat_content.dart';
import 'package:sokoun_app/features/chat/presentation/screens/tenant_chat_empty_screen.dart';
import 'package:sokoun_app/features/chat/presentation/screens/tenant_chat_list_screen.dart';
import 'package:sokoun_app/features/chat/presentation/screens/tenant_chat_restricted_screen.dart';
import 'package:sokoun_app/features/chat/presentation/screens/tenant_chat_search_screen.dart';
import 'package:sokoun_app/features/chat/presentation/screens/tenant_chat_thread_screen.dart';
import 'package:sokoun_app/features/chat/presentation/widgets/chat_list/tenant_chat_list_item.dart';
import 'package:sokoun_app/features/chat/presentation/widgets/chat_thread/tenant_chat_attachments_sheet.dart';
import 'package:sokoun_app/features/chat/presentation/widgets/chat_thread/tenant_chat_message_bubble.dart';
import 'package:sokoun_app/features/chat/presentation/widgets/chat_thread/tenant_chat_voice_recording_bar.dart';
import 'package:sokoun_app/features/chat/presentation/widgets/report/tenant_chat_report_sheet.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivityChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, (call) async {
          return call.method == 'check' ? <String>['wifi'] : null;
        });
    await EasyLocalization.ensureInitialized();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, null);
  });

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _ChatTestAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) {
          return MaterialApp(
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: screen,
          );
        },
      ),
    );
  }

  void configurePhoneViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  testWidgets(
    'opens search and builds the selected conversation with EasyChat',
    (tester) async {
      configurePhoneViewport(tester);

      await tester.pumpWidget(buildScreen(const TenantChatListScreen()));
      await tester.pumpAndSettle();

      expect(find.byType(TenantChatListItem), findsNWidgets(3));

      await tester.tap(find.byKey(const ValueKey('tenant-chat-search-field')));
      await tester.pumpAndSettle();

      expect(find.byType(TenantChatSearchScreen), findsOneWidget);

      await tester.tap(
        find.byKey(const ValueKey('tenant-chat-search-result-1')),
      );
      await tester.pumpAndSettle();

      expect(find.byType(TenantChatThreadScreen), findsOneWidget);
      expect(
        find.byType(EasyChat<List<TenantChatMessageContent>>),
        findsOneWidget,
      );
      expect(find.byType(TenantChatMessageBubble), findsNWidgets(4));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('supports attachments, voice notes, and report submission', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        TenantChatThreadScreen(
          conversation: TenantChatContent.conversations.first,
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('tenant-chat-attachment')));
    await tester.pumpAndSettle();

    expect(find.byType(TenantChatAttachmentsSheet), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('tenant-chat-attachment-photos')),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('tenant-chat-message-101')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('tenant-chat-voice')));
    await tester.pump();

    expect(find.byType(TenantChatVoiceRecordingBar), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('tenant-chat-voice-send')));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('tenant-chat-message-102')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('tenant-chat-report-action')));
    await tester.pumpAndSettle();

    expect(find.byType(TenantChatReportSheet), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('tenant-chat-report-reason-5')));
    await tester.pump();
    await tester.enterText(
      find.byKey(const ValueKey('tenant-chat-report-details')),
      'تفاصيل البلاغ',
    );
    await tester.ensureVisible(
      find.byKey(const ValueKey('tenant-chat-report-submit')),
    );
    await tester.tap(find.byKey(const ValueKey('tenant-chat-report-submit')));
    await tester.pumpAndSettle();

    expect(find.byType(TenantChatListScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shows the empty and restricted chat states', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(const TenantChatListScreen(conversations: [])),
    );
    await tester.pumpAndSettle();

    expect(find.byType(TenantChatEmptyScreen), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(buildScreen(const TenantChatListScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('tenant-chat-3')));
    await tester.pumpAndSettle();

    expect(find.byType(TenantChatRestrictedScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _ChatTestAssetLoader extends AssetLoader {
  const _ChatTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'home': 'الرئيسية',
      'favorites_navigation_saved': 'المحفوظات',
      'chats': 'الشات',
      'notifications': 'الإشعارات',
      'favorites_navigation_account': 'الحساب',
      'verified': 'موثّق',
      'camera': 'الكاميرا',
      'cancel': 'إلغاء',
      'chat_conversations_title': 'المحادثات',
      'chat_search_hint': 'ابحث في المحادثات…',
      'chat_phone_privacy_inbox': 'رقم الموبايل مخفي داخل المحادثات دائماً',
      'chat_empty_title': 'لا محادثات حتى الآن',
      'chat_empty_description':
          'ابدأ بالتحدث مع أصحاب العقارات مباشرةً من صفحة تفاصيل العقار',
      'chat_explore_properties': 'استكشف العقارات',
      'chat_search_results_for': 'نتائج البحث عن',
      'chat_mentioned_properties': 'عقارات مذكورة في المحادثات',
      'chat_active_now': 'نشط الآن',
      'chat_today': 'النهارده',
      'chat_phone_privacy_thread': 'رقم الموبايل مخفي في المحادثة',
      'chat_message_hint': 'اكتب رسالة…',
      'chat_now': 'الآن',
      'chat_send_attachment': 'إرسال مرفق',
      'chat_photos': 'الصور',
      'chat_file': 'ملف',
      'chat_location': 'الموقع',
      'chat_voice_recording': 'جارٍ التسجيل…',
      'chat_restricted_title': 'الشات محدود لحسابات موثّقة',
      'chat_restricted_description':
          'عشان تقدر تتواصل مع الملاك، لازم توثّق هويتك الأول',
      'chat_verified_only_banner': 'الشات لمستخدمين موثّقين فقط',
      'chat_verify_now': 'وثّق الآن',
      'chat_start_kyc': 'ابدأ التوثيق KYC',
      'chat_learn_more_verification': 'اعرف أكتر عن التوثيق',
      'chat_typing_disabled': 'الكتابة معطلة — وثّق أولاً',
      'chat_report_problem_title': 'الإبلاغ عن مشكلة',
      'chat_report_reason_prompt': 'اختار سبب الإبلاغ',
      'chat_report_incorrect_property': 'معلومات العقار غير صحيحة أو مضللة',
      'chat_report_offensive_content': 'محتوى مسيء أو غير لائق',
      'chat_report_potential_fraud': 'احتيال أو نصب محتمل',
      'chat_report_phone_in_photos': 'رقم هاتف ظاهر في الصور',
      'chat_report_unavailable_property': 'عقار غير موجود أو محجوز مسبقاً',
      'chat_report_other_reason': 'سبب آخر',
      'chat_report_details_hint': 'اكتب تفاصيل المشكلة…',
      'chat_report_privacy': 'تقريرك سري ولن يُشارك مع الطرف الآخر',
      'chat_submit_report': 'إرسال البلاغ',
    };
  }
}
