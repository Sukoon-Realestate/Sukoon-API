import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_thread_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_page_response.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_read_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/socket_cubit.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_list_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_restricted_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_search_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_thread_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/previous_chat_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_list/chat_empty_state.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_list/chat_search_field.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_list/chat_list_item.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_message_bubble.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_queued_messages_banner.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_thread_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/report/chat_report_sheet.dart';

const List<ConversationContent> _conversations = [
  ConversationContent(
    id: 'conversation-1',
    name: 'أحمد محمد',
    property: 'شقة مدينة نصر',
    lastMessage: 'ممتاز، العنوان: شارع عباس العقاد...',
    time: '9:30 ص',
    unreadCount: 0,
    isVerified: true,
    isOnline: true,
  ),
  ConversationContent(
    id: 'conversation-2',
    name: 'منى علي',
    property: 'ستوديو التجمع',
    lastMessage: 'متى تريد تعمل الزيارة؟',
    time: 'أمس',
    unreadCount: 2,
    isVerified: true,
    isOnline: false,
  ),
  ConversationContent(
    id: 'conversation-3',
    name: 'كريم طارق',
    property: 'شقة المعادي',
    lastMessage: 'الشقة متاحة للعرض طول الأسبوع',
    time: 'الأثنين',
    unreadCount: 0,
    isVerified: false,
    isOnline: false,
  ),
];

const List<ChatMessageContent> _messages = [
  ChatMessageContent(
    id: 'message-1',
    body: 'أهلاً! الشقة لسه متاحة، تحب تحجز زيارة؟',
    time: '9:10 ص',
    isFromMe: false,
  ),
  ChatMessageContent(
    id: 'message-2',
    body: 'أيوه عايز أزور يوم السبت الساعة 2م',
    time: '9:12 ص',
    isFromMe: true,
  ),
  ChatMessageContent(
    id: 'message-3',
    body: 'تمام، هينفع معايا. هبعتلك تأكيد',
    time: '9:13 ص',
    isFromMe: false,
  ),
  ChatMessageContent(
    id: 'message-4',
    body: 'شكراً جزيلاً',
    time: '9:14 ص',
    isFromMe: true,
  ),
];

int _messagesRequestCount = 0;

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
    await CacheStorage.init();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityChannel, null);
  });

  setUp(() async {
    _messagesRequestCount = 0;
    if (injector.isRegistered<ChatDataSource>()) {
      await injector.unregister<ChatDataSource>();
    }
    injector.registerSingleton<ChatDataSource>(
      const _MemoryChatDataSource(conversations: _conversations),
    );
    await UserTypeHelper.instance.setUserType(UserType.tenant);
    await CacheStorage.write('user', const <String, dynamic>{
      'id': 'f9cf1cdf-50bc-4136-a042-2302ec1513b2',
      'name': 'Current User',
      'phone': '',
      'email': '',
      'type': 'tenant',
    });
  });

  tearDown(() async {
    if (injector.isRegistered<ChatDataSource>()) {
      await injector.unregister<ChatDataSource>();
    }
    await CacheStorage.delete('user');
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
    'opens API-backed search and builds the selected thread with EasyChat',
    (tester) async {
      configurePhoneViewport(tester);

      await tester.pumpWidget(buildScreen(const ChatListScreen()));
      await tester.pumpAndSettle();

      expect(find.byType(ChatListTile), findsNWidgets(3));

      await tester.tap(find.byType(ChatSearchField));
      await tester.pumpAndSettle();

      expect(find.byType(ChatSearchScreen), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('conversation-1')));
      await tester.pumpAndSettle();

      expect(find.byType(ChatScreen), findsOneWidget);
      expect(find.byType(EasyChat<List<ChatMessageContent>>), findsOneWidget);
      expect(find.byType(ChatMessageBubble), findsNWidgets(4));
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('sends optimistically and handles report submission', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(ChatThreadScreen(conversation: _conversations.first)),
    );
    await tester.pumpAndSettle();

    expect(_messagesRequestCount, 1);
    await tester.enterText(find.byType(TextField).first, 'رسالة جديدة');
    await tester.tap(find.byIcon(Icons.send_rounded));
    await tester.pump();

    expect(find.text('رسالة جديدة'), findsOneWidget);
    expect(_messagesRequestCount, 1);

    await tester.tap(find.byIcon(Icons.more_vert_rounded));
    await tester.pumpAndSettle();

    expect(find.byType(ChatReportSheet), findsOneWidget);

    await tester.tap(find.text('سبب آخر'));
    await tester.pump();
    await tester.enterText(find.byType(TextField).last, 'تفاصيل البلاغ');
    await tester.ensureVisible(find.text('إرسال البلاغ'));
    await tester.tap(find.text('إرسال البلاغ'));
    await tester.pumpAndSettle();

    expect(find.byType(ChatListScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('loads message history once for each ChatScreen entry', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(ChatScreen(conversation: _conversations.first)),
    );
    await tester.pumpAndSettle();
    expect(_messagesRequestCount, 1);

    await tester.pump();
    expect(_messagesRequestCount, 1);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    await tester.pumpWidget(
      buildScreen(ChatScreen(conversation: _conversations.first)),
    );
    await tester.pumpAndSettle();
    expect(_messagesRequestCount, 2);
  });

  testWidgets('renders current-user message.new on the physical right', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    final _MemoryChatRealtimeGateway realtime = _MemoryChatRealtimeGateway();
    final ChatThreadCubit cubit = ChatThreadCubit(
      conversationId: _conversations.first.id,
      otherParticipantId: 'other-user-id',
      realtimeService: realtime,
      dataSource: ChatData.source,
    );
    addTearDown(() async {
      await cubit.close();
      await realtime.close();
    });
    final ChatThreadData chatThreadData = ChatThreadData(
      conversationId: _conversations.first.id,
      dataSource: ChatData.source,
    );
    final Future<List<ChatMessageContent>> initialMessagesRequest =
        chatThreadData.loadInitialMessages();

    await tester.pumpWidget(
      buildScreen(
        BlocProvider<ChatThreadCubit>.value(
          value: cubit,
          child: Scaffold(
            body: ChatThreadContent(
              conversation: _conversations.first,
              initialMessagesRequest: initialMessagesRequest,
              messagesCacheKey: chatThreadData.messagesCacheKey,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await cubit.connect();

    final ChatSocketMessage ownMessage = ChatSocketMessage.fromJson(const {
      'id': 'socket-own-message',
      'conversation': 'conversation-1',
      'sender': {
        'id': 'f9cf1cdf-50bc-4136-a042-2302ec1513b2',
        'full_name': 'Current User',
        'avatar_url': '',
        'is_online': true,
      },
      'content': 'Own socket message',
      'created_at': '2026-09-16T10:00:00Z',
    });
    expect(ownMessage.isFromMe, isTrue);

    realtime.addMessage(ownMessage);
    await tester.pumpAndSettle();

    final Finder messageText = find.text('Own socket message');
    final Finder messageBubble = find.ancestor(
      of: messageText,
      matching: find.byType(ChatMessageBubble),
    );
    expect(messageText, findsOneWidget);
    expect(messageBubble, findsOneWidget);
    expect(tester.widget<ChatMessageBubble>(messageBubble).isFromMe, isTrue);

    final Rect contentRect = tester.getRect(find.byType(ChatThreadContent));
    expect(
      tester.getCenter(messageBubble).dx,
      greaterThan(contentRect.center.dx),
    );
    expect(_messagesRequestCount, 1);
  });

  testWidgets('shows queued messages while the chat is offline', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    final _MemoryChatRealtimeGateway realtime = _MemoryChatRealtimeGateway(
      canConnect: false,
    );
    final ChatThreadCubit cubit = ChatThreadCubit(
      conversationId: _conversations.first.id,
      otherParticipantId: 'other-user-id',
      realtimeService: realtime,
      dataSource: ChatData.source,
    );
    addTearDown(() async {
      await cubit.close();
      await realtime.close();
    });
    final ChatThreadData chatThreadData = ChatThreadData(
      conversationId: _conversations.first.id,
      dataSource: ChatData.source,
    );

    await tester.pumpWidget(
      buildScreen(
        BlocProvider<ChatThreadCubit>.value(
          value: cubit,
          child: Scaffold(
            body: ChatThreadContent(
              conversation: _conversations.first,
              initialMessagesRequest: chatThreadData.loadInitialMessages(),
              messagesCacheKey: chatThreadData.messagesCacheKey,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).first, 'رسالة بدون اتصال');
    await tester.tap(find.byIcon(Icons.send_rounded));
    await tester.pump();

    expect(cubit.state.queuedMessageCount, 1);
    expect(find.byType(ChatQueuedMessagesBanner), findsOneWidget);
    expect(find.text('سيتم إرسال الرسائل عند عودة الاتصال'), findsOneWidget);
    expect(find.byIcon(Icons.schedule_send_rounded), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('previous chat loads history without composer actions', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(PreviousChatScreen(conversation: _conversations.first)),
    );
    await tester.pumpAndSettle();

    expect(_messagesRequestCount, 1);
    expect(find.byType(EasyChat<List<ChatMessageContent>>), findsOneWidget);
    expect(find.byIcon(Icons.send_rounded), findsNothing);
    expect(find.byIcon(Icons.more_vert_rounded), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shows the API empty and restricted chat states', (tester) async {
    configurePhoneViewport(tester);
    await injector.unregister<ChatDataSource>();
    injector.registerSingleton<ChatDataSource>(
      const _MemoryChatDataSource(conversations: []),
    );

    await tester.pumpWidget(buildScreen(const ChatListScreen()));
    await tester.pumpAndSettle();

    expect(find.byType(ChatEmptyState), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(const SizedBox.shrink());
    await injector.unregister<ChatDataSource>();
    injector.registerSingleton<ChatDataSource>(
      const _MemoryChatDataSource(conversations: _conversations),
    );
    await tester.pumpWidget(buildScreen(const ChatListScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('conversation-3')));
    await tester.pumpAndSettle();

    expect(find.byType(ChatRestrictedScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

class _MemoryChatDataSource implements ChatDataSource {
  const _MemoryChatDataSource({required this.conversations});

  final List<ConversationContent> conversations;

  @override
  String? get conversationsCacheKey => null;

  @override
  String? messagesCacheKey(String conversationId) => null;

  @override
  Future<(List<ConversationContent>, PaginationData)> getConversationsPage({
    required int page,
  }) async {
    return (
      page == 1 ? conversations : const <ConversationContent>[],
      PaginationData(perPage: conversations.length, totalPages: 1),
    );
  }

  @override
  Future<ChatPageResponse<ConversationContent>> getConversations({
    required int page,
    int pageSize = ChatData.conversationsPageSize,
  }) async {
    return ChatPageResponse<ConversationContent>(
      count: conversations.length,
      next: null,
      previous: null,
      results: conversations,
      page: page,
      pageSize: pageSize,
    );
  }

  @override
  Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    required int page,
  }) async {
    _messagesRequestCount++;
    return (
      page == 1 ? _messages : const <ChatMessageContent>[],
      PaginationData(perPage: _messages.length, totalPages: 1),
    );
  }

  @override
  Future<ConversationContent> createConversation(String userId) async =>
      conversations.first;

  @override
  Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    return ChatMessageContent(
      id: 'sent-message',
      body: content,
      time: '9:15 ص',
      isFromMe: true,
      conversationId: conversationId,
    );
  }

  @override
  Future<ChatReadContent> markConversationAsRead(String conversationId) async =>
      const ChatReadContent(status: 'read');
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
      'cancel': 'إلغاء',
      'chat_conversations_title': 'المحادثات',
      'chat_search_hint': 'ابحث في المحادثات…',
      'chat_phone_privacy_inbox': 'رقم الموبايل مخفي داخل المحادثات دائماً',
      'chat_empty_title': 'لا محادثات حتى الآن',
      'chat_empty_description':
          'ابدأ بالتحدث مع أصحاب العقارات مباشرةً من صفحة تفاصيل العقار',
      'chat_explore_properties': 'استكشف العقارات',
      'chat_search_results_for': 'نتائج البحث عن',
      'chat_search_empty_title': 'لا توجد محادثات مطابقة',
      'chat_search_empty_description': 'جرّب اسماً أو كلمة بحث مختلفة',
      'chat_mentioned_properties': 'عقارات مذكورة في المحادثات',
      'chat_active_now': 'نشط الآن',
      'chat_today': 'النهارده',
      'chat_phone_privacy_thread': 'رقم الموبايل مخفي في المحادثة',
      'chat_message_hint': 'اكتب رسالة…',
      'chat_send_message': 'إرسال الرسالة',
      'chat_messages_empty_title': 'لا توجد رسائل حتى الآن',
      'chat_messages_empty_description': 'أرسل أول رسالة لبدء المحادثة',
      'chat_now': 'الآن',
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
      'waiting_for_connection': 'جارٍ الاتصال...',
      'chat_queued_messages': 'سيتم إرسال الرسائل عند عودة الاتصال',
    };
  }
}

class _MemoryChatRealtimeGateway implements ChatRealtimeGateway {
  _MemoryChatRealtimeGateway({this.canConnect = true});

  final bool canConnect;
  final StreamController<ChatSocketMessage> _messages =
      StreamController<ChatSocketMessage>.broadcast(sync: true);
  final StreamController<ChatReadReceipt> _readReceipts =
      StreamController<ChatReadReceipt>.broadcast(sync: true);
  final StreamController<ChatRealtimeStatus> _statuses =
      StreamController<ChatRealtimeStatus>.broadcast(sync: true);

  @override
  String? activeConversationId;

  @override
  bool isConnected = false;

  @override
  Stream<ChatSocketMessage> get messages => _messages.stream;

  @override
  Stream<ChatReadReceipt> get readReceipts => _readReceipts.stream;

  @override
  ChatRealtimeStatus get status => isConnected
      ? ChatRealtimeStatus.connected
      : ChatRealtimeStatus.disconnected;

  @override
  Stream<ChatRealtimeStatus> get statuses => _statuses.stream;

  void addMessage(ChatSocketMessage message) => _messages.add(message);

  @override
  Future<void> connect() async {
    if (!canConnect) {
      isConnected = false;
      _statuses.add(ChatRealtimeStatus.disconnected);
      return;
    }
    isConnected = true;
    _statuses.add(ChatRealtimeStatus.connected);
  }

  @override
  Future<void> disconnect() async {
    isConnected = false;
    _statuses.add(ChatRealtimeStatus.disconnected);
  }

  @override
  Future<void> markConversationAsRead(String conversationId) async {}

  @override
  Future<void> sendMessage({
    required String conversationId,
    required String content,
  }) async {}

  @override
  void setActiveConversation(String? conversationId) {
    activeConversationId = conversationId;
  }

  Future<void> close() async {
    await Future.wait([
      _messages.close(),
      _readReceipts.close(),
      _statuses.close(),
    ]);
  }
}
