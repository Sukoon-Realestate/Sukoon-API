import 'package:sokoun_app/features/shared/chat/data/models/chat_message_acknowledgement.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_local_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_local_state.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/chat_builder/chat_message.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_day_label.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/widgets/chat_builder/easy_chat.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_socket_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_thread_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_page_response.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_read_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_thread_cubit.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chats_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_restricted_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_search_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/previous_chat_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_list/chat_empty_state.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_list/chat_search_field.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_list_tile.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_message_bubble.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_queued_messages_banner.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/chat_thread/chat_thread_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/report/chat_report_sheet.dart';
import 'package:sokoun_app/features/shared/notifications/data/foreground_notification_bus.dart';

import 'helpers/recording_chat_socket.dart';

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
int _conversationsRequestCount = 0;
int _contactRequestCount = 0;
ConversationContent? _contactConversation;
bool _contactFailure = false;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivityChannel = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );

  setUpAll(() async {
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: _ReportRepository()),
    );
    injector.registerSingleton<WorkspaceCubit>(WorkspaceCubit());
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          (call) async => null,
        );
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
    _reportRequests.clear();
    _reportFailure = false;
    _reportReceiptMissing = false;
    _messagesRequestCount = 0;
    _conversationsRequestCount = 0;
    _contactRequestCount = 0;
    _contactConversation = null;
    _contactFailure = false;
    if (injector.isRegistered<ChatDataSource>()) {
      await injector.unregister<ChatDataSource>();
    }
    injector.registerSingleton<ChatDataSource>(
      const _MemoryChatDataSource(conversations: _conversations),
    );
    await UserTypeHelper.instance.setUserType(UserType.tenant);
    await CacheStorage.write('user', const <String, dynamic>{
      'is_verified': true,
      'id': 'f9cf1cdf-50bc-4136-a042-2302ec1513b2',
      'name': 'Current User',
      'phone': '',
      'email': '',
      'type': 'tenant',
    });
  });

  tearDown(() async {
    ChatRealtimeService.instance.setActiveConversation(null);
    await ChatRealtimeService.instance.disconnect();
    if (injector.isRegistered<ChatSocketDataSource>()) {
      await injector.unregister<ChatSocketDataSource>();
    }
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
            navigatorObservers: [AppNavigationObserver.instance],
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

  for (final bool fromSearch in [false, true]) {
    testWidgets(
      'refreshes conversations once after returning from ${fromSearch ? 'search and chat' : 'chat'}',
      (tester) async {
        configurePhoneViewport(tester);
        final sockets = RecordingChatSocketSource()..echoSentMessages = true;
        injector.registerSingleton<ChatSocketDataSource>(sockets);
        await tester.pumpWidget(buildScreen(const ChatsScreen()));
        await tester.pumpAndSettle();
        expect(_conversationsRequestCount, 1);
        if (fromSearch) {
          await tester.tap(find.byType(ChatSearchField));
          await tester.pumpAndSettle();
          await tester.tap(find.byKey(const ValueKey('conversation-1')));
        } else {
          await tester.tap(find.byType(ChatListTile).first);
        }
        await tester.pumpAndSettle();
        expect(find.byType(ChatScreen), findsOneWidget);
        expect(_conversationsRequestCount, 1);

        for (final message in ['Hello', 'Another message']) {
          await tester.enterText(find.byType(TextField).first, message);
          await tester.pump();
          await tester.tap(find.byIcon(Icons.send_rounded));
          await tester.pumpAndSettle();
          expect(_conversationsRequestCount, 1);
          expect(
            find.text('سيتم إرسال الرسائل عند عودة الاتصال'),
            findsNothing,
          );
        }
        expect(sockets.sentMessages, 2);
        await sockets.receive(
          const ChatSocketMessage.initial().copyWith(
            id: 'incoming-message',
            conversationId: 'conversation-1',
            content: 'Reply',
            sender: const ChatParticipantContent.initial().copyWith(
              id: 'other-user',
            ),
          ),
        );
        ForegroundNotificationBus.receive({
          'notification_type': 'new_message',
          'message_id': 'incoming-message',
          'conversation_id': 'conversation-1',
        });
        await tester.pumpAndSettle();
        expect(_conversationsRequestCount, 1);

        Go.back();
        await tester.pumpAndSettle();
        if (fromSearch) {
          expect(find.byType(ChatSearchScreen), findsOneWidget);
          expect(_conversationsRequestCount, 1);
          Go.back();
          await tester.pumpAndSettle();
        }
        expect(find.byType(ChatsScreen), findsOneWidget);
        expect(_conversationsRequestCount, 2);
        await tester.pump(const Duration(seconds: 2));
        expect(_conversationsRequestCount, 2);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pumpAndSettle();
      },
    );
  }

  testWidgets('closing search without a chat does not refetch conversations', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(buildScreen(const ChatsScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(ChatSearchField));
    await tester.pumpAndSettle();
    Go.back();
    await tester.pumpAndSettle();
    expect(_conversationsRequestCount, 1);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });

  testWidgets(
    'opens API-backed search and builds the selected thread with EasyChat',
    (tester) async {
      configurePhoneViewport(tester);

      await tester.pumpWidget(buildScreen(const ChatsScreen()));
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

  for (final missingReceipt in [false, true]) {
    testWidgets(
      'report ${missingReceipt ? 'without receipt' : 'failure'} retains details and permits retry',
      (tester) async {
        configurePhoneViewport(tester);
        await tester.pumpWidget(
          buildScreen(ChatScreen(conversation: _conversations.first)),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.byIcon(Icons.more_vert_rounded));
        await tester.pumpAndSettle();
        await tester.tap(find.text('سبب آخر'));
        await tester.pump();
        await tester.enterText(
          find.byType(TextField).last,
          'Keep these report details',
        );
        _reportFailure = !missingReceipt;
        _reportReceiptMissing = missingReceipt;
        await tester.ensureVisible(find.text('إرسال البلاغ'));
        await tester.tap(find.text('إرسال البلاغ'));
        await tester.pumpAndSettle();
        expect(find.byType(ChatReportSheet), findsOneWidget);
        expect(find.text('Keep these report details'), findsOneWidget);
        expect(_reportRequests, hasLength(1));
        _reportFailure = false;
        _reportReceiptMissing = false;
        await tester.tap(find.text('إرسال البلاغ'));
        await tester.pumpAndSettle();
        expect(find.byType(ChatReportSheet), findsNothing);
        expect(find.byType(ChatScreen), findsOneWidget);
        expect(_reportRequests, hasLength(2));
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('sends optimistically and handles report submission', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(ChatScreen(conversation: _conversations.first)),
    );
    await tester.pumpAndSettle();

    expect(_messagesRequestCount, 1);
    await tester.enterText(find.byType(TextField).first, 'رسالة جديدة');
    await tester.pump();
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

    expect(find.byType(ChatReportSheet), findsNothing);
    expect(find.byType(ChatScreen), findsOneWidget);
    expect(_reportRequests, hasLength(1));
    expect(_reportRequests.single['category'], 'report_owner');
    expect(
      _reportRequests.single['description'],
      contains(_conversations.first.id),
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('chat entry, exit and app lifecycle own the socket connection', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    final sockets = RecordingChatSocketSource();
    injector.registerSingleton<ChatSocketDataSource>(sockets);
    await tester.pumpWidget(
      buildScreen(ChatScreen(conversation: _conversations.first)),
    );
    await tester.pumpAndSettle();
    expect(sockets.connections, 1);
    expect(sockets.readRequests, 1);
    expect(_messagesRequestCount, 1);

    for (final state in [
      AppLifecycleState.inactive,
      AppLifecycleState.hidden,
      AppLifecycleState.paused,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(state);
    }
    await tester.pumpAndSettle();
    expect(sockets.disconnections, 1);
    expect(ChatRealtimeService.instance.isConnected, isFalse);
    for (final state in [
      AppLifecycleState.hidden,
      AppLifecycleState.inactive,
      AppLifecycleState.resumed,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(state);
    }
    await tester.pumpAndSettle();
    expect(sockets.connections, 2);
    expect(sockets.readRequests, 2);
    expect(_messagesRequestCount, 1);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    expect(sockets.disconnections, 2);
    expect(ChatRealtimeService.instance.isConnected, isFalse);
    expect(ChatRealtimeService.instance.activeConversationId, isNull);
  });

  testWidgets(
    'accepted contact refresh removes hidden copy without reloading messages',
    (tester) async {
      configurePhoneViewport(tester);
      final sockets = RecordingChatSocketSource();
      injector.registerSingleton<ChatSocketDataSource>(sockets);
      final hidden = _conversations.first.copyWith(
        otherParticipant: const ChatParticipantContent(id: 'owner'),
      );
      _contactConversation = hidden;
      await tester.pumpWidget(buildScreen(ChatScreen(conversation: hidden)));
      await tester.pumpAndSettle();
      expect(find.text('رقم الموبايل مخفي في المحادثة'), findsOneWidget);
      expect(find.text('+201001234567'), findsNothing);
      expect(_contactRequestCount, 1);

      _contactConversation = hidden.copyWith(
        otherParticipant: hidden.otherParticipant.copyWith(
          phoneNumber: '+201001234567',
          isPhoneRevealed: true,
        ),
      );
      ForegroundNotificationBus.receive({
        'notification_type': 'visit_accepted',
        'notification_id': 'contact-accepted',
        'visit_id': 'visit',
        'conversation_id': hidden.id,
      });
      await tester.pumpAndSettle();
      expect(find.text('+201001234567'), findsOneWidget);
      expect(find.text('رقم الموبايل مخفي في المحادثة'), findsNothing);
      expect(_messagesRequestCount, 1);

      _contactConversation = hidden;
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();
      expect(find.text('+201001234567'), findsNothing);
      expect(find.text('رقم الموبايل مخفي في المحادثة'), findsOneWidget);
      expect(_messagesRequestCount, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('failed contact refresh cannot reveal a raw phone', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    _contactFailure = true;
    final hidden = _conversations.first.copyWith(
      otherParticipant: const ChatParticipantContent(
        id: 'owner',
        phoneNumber: '+201001234567',
      ),
    );
    await tester.pumpWidget(buildScreen(ChatScreen(conversation: hidden)));
    await tester.pumpAndSettle();
    expect(find.text('+201001234567'), findsNothing);
    expect(find.text('رقم الموبايل مخفي في المحادثة'), findsOneWidget);
    expect(_messagesRequestCount, 1);
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
      localStore: _MemoryChatLocalStore(),
      dataSource: ChatData.source,
    );
    addTearDown(() async {
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.runAsync(() async {
        await cubit.close();
        await realtime.close();
      });
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
    final connecting = cubit.connect();
    await tester.pump();
    await connecting;

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

  testWidgets(
    'numeric socket conversation references inject replies into Pagify once',
    (tester) async {
      configurePhoneViewport(tester);
      final sockets = RecordingChatSocketSource();
      injector.registerSingleton<ChatSocketDataSource>(sockets);
      final conversation = _conversations.first.copyWith(
        id: 'da0be73d-2274-44ed-b419-2d3fc6c16f58',
        otherParticipant: const ChatParticipantContent.initial().copyWith(
          id: '4f5bd135-df44-409f-a2cf-712d8fc1fce8',
        ),
      );
      await tester.pumpWidget(
        buildScreen(ChatScreen(conversation: conversation)),
      );
      await tester.pumpAndSettle();
      final chat = tester.widget<EasyChat<List<ChatMessageContent>>>(
        find.byType(EasyChat<List<ChatMessageContent>>),
      );
      final initialCount = chat.controller.items.length;
      final initialReadRequests = sockets.readRequests;
      final message = ChatSocketMessage.fromJson(const {
        'id': '7392fcae-aac6-460d-8e8c-d9c2b332ade4',
        'conversation': 5,
        'sender': {
          'id': '4f5bd135-df44-409f-a2cf-712d8fc1fce8',
          'first_name': 'Other',
          'last_name': 'User',
          'full_name': 'Other User',
          'avatar_url': '',
          'is_online': true,
        },
        'content': 'jjjjjj',
        'client_message_id': '6de5f26e-2261-4d05-8358-4a58884d4ec6',
        'status': 'sent',
        'created_at': '2026-10-08T04:31:49.225361+03:00',
      });

      await sockets.receive(message);
      await tester.pumpAndSettle();

      expect(chat.controller.items, hasLength(initialCount + 1));
      expect(chat.controller.items.last.message.id, message.id);
      expect(chat.controller.items.last.sender.isFromMe, isFalse);
      expect(find.text('jjjjjj'), findsOneWidget);
      expect(sockets.readRequests, initialReadRequests + 1);

      await sockets.receive(message);
      await sockets.receive(
        message.copyWith(
          id: 'another-participant-message',
          sender: const ChatParticipantContent.initial().copyWith(
            id: 'unrelated-user-id',
          ),
        ),
      );
      await sockets.receive(
        message.copyWith(
          id: 'another-conversation-message',
          conversationId: 'e2a3b7ef-cfcc-4be0-bfc7-22ea7253c55e',
        ),
      );
      await tester.pumpAndSettle();

      expect(chat.controller.items, hasLength(initialCount + 1));
      expect(find.text('jjjjjj'), findsOneWidget);
      expect(_messagesRequestCount, 1);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    },
  );

  testWidgets(
    'incoming messages preserve older reading position and use real days',
    (tester) async {
      configurePhoneViewport(tester);
      final realtime = _MemoryChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: _conversations.first.id,
        otherParticipantId: 'other-user-id',
        realtimeService: realtime,
        localStore: _MemoryChatLocalStore(),
        dataSource: ChatData.source,
      );
      addTearDown(() async {
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.runAsync(() async {
          await cubit.close();
          await realtime.close();
        });
      });
      final messages = List.generate(
        40,
        (index) => ChatMessageContent(
          id: 'history-$index',
          body: 'Earlier message $index',
          time: '',
          createdAt: DateTime(2026, 9, index < 20 ? 16 : 15, 12, 40 - index),
          isFromMe: false,
        ),
      );
      await tester.pumpWidget(
        buildScreen(
          BlocProvider<ChatThreadCubit>.value(
            value: cubit,
            child: Scaffold(
              body: ChatThreadContent(
                conversation: _conversations.first,
                initialMessagesRequest: Future.value(messages),
                messagesCacheKey: null,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final connecting = cubit.connect();
      await tester.pump();
      await connecting;
      final list = find.byType(EasyChat<List<ChatMessageContent>>);
      final position = tester
          .state<ScrollableState>(
            find.descendant(of: list, matching: find.byType(Scrollable)).first,
          )
          .position;
      expect(position.extentAfter, 0);
      await tester.drag(list, const Offset(0, 450));
      await tester.pumpAndSettle();
      final offset = position.pixels;
      expect(position.extentAfter, greaterThan(80));
      realtime.addMessage(
        const ChatSocketMessage.initial().copyWith(
          id: 'new-while-reading',
          conversationId: _conversations.first.id,
          content: 'Incoming reply',
          createdAt: DateTime(2026, 9, 17),
          sender: const ChatParticipantContent.initial().copyWith(
            id: 'other-user-id',
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(position.pixels, closeTo(offset, .1));
      expect(
        tester
            .widget<EasyChat<List<ChatMessageContent>>>(list)
            .controller
            .items
            .last
            .message
            .id,
        'new-while-reading',
      );
      position.jumpTo(0);
      await tester.pumpAndSettle();
      expect(
        tester.widget<ChatDayLabel>(find.byType(ChatDayLabel).first).date.day,
        15,
      );
      expect(find.text('النهارده'), findsNothing);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );

  testWidgets('long message body remains fully readable', (tester) async {
    configurePhoneViewport(tester);
    final body = List.generate(15, (index) => 'Message line $index').join('\n');
    await tester.pumpWidget(
      buildScreen(
        Scaffold(
          body: Align(
            child: ChatMessageBubble(
              message: ChatMessages(
                message: Message(id: 'long', type: 'text', body: body),
                sender: Sender(
                  id: 'other',
                  name: '',
                  image: '',
                  isFromMe: false,
                ),
              ),
              isFromMe: false,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final text = tester.widget<AppText>(
      find.ancestor(of: find.text(body), matching: find.byType(AppText)),
    );
    expect(text.maxLines, isNull);
    expect(tester.getSize(find.text(body)).height, greaterThan(200));
    expect(tester.takeException(), isNull);
  });

  for (final bool offline in [true, false]) {
    testWidgets(
      offline
          ? 'shows queued messages while the chat is offline'
          : 'shows the queued-message banner after a two-second send delay',
      (tester) async {
        configurePhoneViewport(tester);
        final _MemoryChatRealtimeGateway realtime = _MemoryChatRealtimeGateway(
          canConnect: !offline,
        );
        final ChatThreadCubit cubit = ChatThreadCubit(
          conversationId: _conversations.first.id,
          otherParticipantId: 'other-user-id',
          realtimeService: realtime,
          localStore: _MemoryChatLocalStore(),
          dataSource: ChatData.source,
        );
        addTearDown(() async {
          await tester.pumpWidget(const SizedBox.shrink());
          await tester.runAsync(() async {
            await cubit.close();
            await realtime.close();
          });
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

        await tester.enterText(
          find.byType(TextField).first,
          'رسالة بدون اتصال',
        );
        await tester.pump();
        await tester.tap(find.byIcon(Icons.send_rounded));
        await tester.pump();

        expect(cubit.state.queuedMessageCount, 1);
        expect(find.byType(ChatQueuedMessagesBanner), findsOneWidget);
        if (!offline) {
          expect(
            find.text('سيتم إرسال الرسائل عند عودة الاتصال'),
            findsNothing,
          );
          await tester.pump(const Duration(milliseconds: 1999));
          expect(
            find.text('سيتم إرسال الرسائل عند عودة الاتصال'),
            findsNothing,
          );
          await tester.pump(const Duration(milliseconds: 1));
        }
        expect(
          find.text('سيتم إرسال الرسائل عند عودة الاتصال'),
          findsOneWidget,
        );
        expect(find.byIcon(Icons.schedule_send_rounded), findsOneWidget);
        if (!offline) {
          realtime.addMessage(
            const ChatSocketMessage.initial().copyWith(
              id: 'confirmed-delayed-message',
              clientMessageId: realtime.lastClientMessageId,
              conversationId: 'conversation-1',
              content: 'رسالة بدون اتصال',
              sender: const ChatParticipantContent.initial().copyWith(
                id: 'f9cf1cdf-50bc-4136-a042-2302ec1513b2',
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(
            find.text('سيتم إرسال الرسائل عند عودة الاتصال'),
            findsNothing,
          );
        }
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.runAsync(cubit.close);
        await tester.pumpAndSettle();
      },
    );
  }

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

  testWidgets(
    'participant verification does not grant or deny current account messaging',
    (tester) async {
      configurePhoneViewport(tester);
      await injector.unregister<ChatDataSource>();
      injector.registerSingleton<ChatDataSource>(
        const _MemoryChatDataSource(conversations: []),
      );

      await tester.pumpWidget(buildScreen(const ChatsScreen()));
      await tester.pumpAndSettle();

      expect(find.byType(ChatEmptyState), findsOneWidget);
      expect(tester.takeException(), isNull);

      await tester.pumpWidget(const SizedBox.shrink());
      await injector.unregister<ChatDataSource>();
      injector.registerSingleton<ChatDataSource>(
        const _MemoryChatDataSource(conversations: _conversations),
      );
      await tester.pumpWidget(buildScreen(const ChatsScreen()));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('conversation-3')));
      await tester.pumpAndSettle();

      expect(find.byType(ChatScreen), findsOneWidget);
      expect(find.byType(ChatRestrictedScreen), findsNothing);
      expect(tester.takeException(), isNull);
    },
  );
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
    _conversationsRequestCount++;
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
  Future<ConversationContent> getConversation(String conversationId) async {
    _contactRequestCount++;
    if (_contactFailure) throw StateError('Contact unavailable');
    return _contactConversation ??
        conversations.firstWhere((item) => item.id == conversationId);
  }

  @override
  Future<ConversationContent> createConversation(String userId) async =>
      conversations.first;

  @override
  Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
    String clientMessageId = '',
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
  String lastClientMessageId = '';
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
  Stream<ChatMessageAcknowledgement> get acknowledgements =>
      const Stream.empty();

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
    String clientMessageId = '',
  }) async {
    lastClientMessageId = clientMessageId;
  }

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

final List<Map<String, dynamic>> _reportRequests = [];
bool _reportFailure = false;
bool _reportReceiptMissing = false;

class _ReportRepository implements BaseRepository {
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (params.api != ApiConstants.supportTickets) {
      throw StateError('Unexpected report request');
    }
    _reportRequests.add(Map.of(params.body!));
    if (_reportFailure) {
      return const Error(ServerFailure('Report could not be saved'));
    }
    return Success(
      BaseModel(
        key: 'success',
        msg: '',
        data: params.mapper!({
          'id': 'ticket-1',
          'reference': _reportReceiptMissing ? '' : 'SUP-001',
          'subject': params.body!['subject'],
          'status': 'open',
          'created_at': '2026-10-06T10:00:00Z',
          'messages': [
            {
              'id': 'message-1',
              'sender': 'user',
              'body': params.body!['description'],
              'created_at': '2026-10-06T10:00:00Z',
              'attachments': [],
            },
          ],
        }),
      ),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _MemoryChatLocalStore implements ChatLocalStore {
  ChatLocalState state = const ChatLocalState.initial();
  @override
  Future<ChatLocalState> read() async => state;
  @override
  Future<void> write(ChatLocalState next) async {
    state = next;
  }
}
