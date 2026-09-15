import 'package:equatable/equatable.dart';

class ChatParticipantContent extends Equatable {
  const ChatParticipantContent({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.email,
    required this.avatarUrl,
    required this.isOnline,
    this.isVerified = true,
  });

  const ChatParticipantContent.initial()
    : id = '',
      firstName = '',
      lastName = '',
      fullName = '',
      email = '',
      avatarUrl = '',
      isOnline = false,
      isVerified = true;

  factory ChatParticipantContent.fromJson(Map<String, dynamic> json) {
    final String firstName = json['first_name']?.toString() ?? '';
    final String lastName = json['last_name']?.toString() ?? '';
    final String composedName = [
      firstName,
      lastName,
    ].where((part) => part.trim().isNotEmpty).join(' ');
    return ChatParticipantContent(
      id: json['id']?.toString() ?? '',
      firstName: firstName,
      lastName: lastName,
      fullName: json['full_name']?.toString().trim().isNotEmpty == true
          ? json['full_name'].toString()
          : composedName,
      email: json['email']?.toString() ?? '',
      avatarUrl: json['avatar_url']?.toString() ?? '',
      isOnline: json['is_online'] == true,
      isVerified: json['is_verified'] != false,
    );
  }

  final String id;
  final String firstName;
  final String lastName;
  final String fullName;
  final String email;
  final String avatarUrl;
  final bool isOnline;
  final bool isVerified;

  Map<String, dynamic> toJson() => {
    'id': id,
    'first_name': firstName,
    'last_name': lastName,
    'full_name': fullName,
    'email': email,
    'avatar_url': avatarUrl,
    'is_online': isOnline,
    'is_verified': isVerified,
  };

  @override
  List<Object?> get props => [
    id,
    firstName,
    lastName,
    fullName,
    email,
    avatarUrl,
    isOnline,
    isVerified,
  ];
}

class ConversationContent extends Equatable {
  const ConversationContent({
    required this.id,
    required this.name,
    required this.property,
    required this.lastMessage,
    required this.time,
    required this.unreadCount,
    required this.isVerified,
    required this.isOnline,
    this.otherParticipant = const ChatParticipantContent.initial(),
    this.lastMessageAt,
    this.updatedAt,
  });

  factory ConversationContent.initial() => const ConversationContent(
    id: 0,
    name: '',
    property: '',
    lastMessage: '',
    time: '',
    unreadCount: 0,
    isVerified: false,
    isOnline: false,
  );

  factory ConversationContent.fromJson(Map<String, dynamic> json) {
    final Object? participantJson = json['other_participant'];
    final ChatParticipantContent participant = ChatParticipantContent.fromJson(
      participantJson is Map
          ? Map<String, dynamic>.from(participantJson)
          : const <String, dynamic>{},
    );
    final String apiName = participant.fullName;
    final DateTime? lastMessageAt = DateTime.tryParse(
      json['last_message_at']?.toString() ?? '',
    );
    return ConversationContent(
      id: json['id'] ?? '',
      name: apiName.isNotEmpty ? apiName : json['name']?.toString() ?? '',
      property: json['property']?.toString() ?? '',
      lastMessage:
          json['last_message_preview']?.toString() ??
          json['last_message']?.toString() ??
          '',
      time: json['time']?.toString() ?? '',
      unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
      isVerified: participantJson is Map
          ? participant.isVerified
          : json['is_verified'] == true,
      isOnline: participantJson is Map
          ? participant.isOnline
          : json['is_online'] == true,
      otherParticipant: participant,
      lastMessageAt: lastMessageAt,
      updatedAt: DateTime.tryParse(json['updated_at']?.toString() ?? ''),
    );
  }

  final Object id;
  final String name;
  final String property;
  final String lastMessage;
  final String time;
  final int unreadCount;
  final bool isVerified;
  final bool isOnline;
  final ChatParticipantContent otherParticipant;
  final DateTime? lastMessageAt;
  final DateTime? updatedAt;

  bool matchesQuery(String query) {
    final String normalizedQuery = query.trim().toLowerCase();
    if (normalizedQuery.isEmpty) {
      return true;
    }

    return name.toLowerCase().contains(normalizedQuery) ||
        property.toLowerCase().contains(normalizedQuery) ||
        lastMessage.toLowerCase().contains(normalizedQuery);
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'other_participant': otherParticipant.toJson(),
      'name': name,
      if (property.isNotEmpty) 'property': property,
      'last_message_preview': lastMessage,
      'time': time,
      'unread_count': unreadCount,
      'is_verified': isVerified,
      'is_online': isOnline,
      'last_message_at': lastMessageAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  ConversationContent copyWith({
    Object? id,
    String? name,
    String? property,
    String? lastMessage,
    String? time,
    int? unreadCount,
    bool? isVerified,
    bool? isOnline,
    ChatParticipantContent? otherParticipant,
    DateTime? lastMessageAt,
    DateTime? updatedAt,
  }) {
    return ConversationContent(
      id: id ?? this.id,
      name: name ?? this.name,
      property: property ?? this.property,
      lastMessage: lastMessage ?? this.lastMessage,
      time: time ?? this.time,
      unreadCount: unreadCount ?? this.unreadCount,
      isVerified: isVerified ?? this.isVerified,
      isOnline: isOnline ?? this.isOnline,
      otherParticipant: otherParticipant ?? this.otherParticipant,
      lastMessageAt: lastMessageAt ?? this.lastMessageAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    name,
    property,
    lastMessage,
    time,
    unreadCount,
    isVerified,
    isOnline,
    otherParticipant,
    lastMessageAt,
    updatedAt,
  ];
}

class ChatMessageContent extends Equatable {
  const ChatMessageContent({
    required this.id,
    required this.body,
    required this.time,
    required this.isFromMe,
    this.type = 'text',
    this.conversationId = '',
    this.sender = const ChatParticipantContent.initial(),
    this.createdAt,
  });

  factory ChatMessageContent.initial() =>
      const ChatMessageContent(id: 0, body: '', time: '', isFromMe: false);

  factory ChatMessageContent.fromJson(Map<String, dynamic> json) {
    final Object? senderJson = json['sender'];
    return ChatMessageContent(
      id: json['id'] ?? '',
      body: json['content']?.toString() ?? json['body']?.toString() ?? '',
      time: json['time']?.toString() ?? '',
      isFromMe: json['is_from_me'] == true,
      type: json['type']?.toString() ?? 'text',
      conversationId:
          json['conversation_id']?.toString() ??
          json['conversation']?.toString() ??
          '',
      sender: ChatParticipantContent.fromJson(
        senderJson is Map
            ? Map<String, dynamic>.from(senderJson)
            : const <String, dynamic>{},
      ),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
    );
  }

  final Object id;
  final String body;
  final String time;
  final bool isFromMe;
  final String type;
  final String conversationId;
  final ChatParticipantContent sender;
  final DateTime? createdAt;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'conversation': conversationId,
      'sender': sender.toJson(),
      'content': body,
      'created_at': createdAt?.toIso8601String(),
      'body': body,
      'time': time,
      'is_from_me': isFromMe,
      'type': type,
    };
  }

  ChatMessageContent copyWith({
    Object? id,
    String? body,
    String? time,
    bool? isFromMe,
    String? type,
    String? conversationId,
    ChatParticipantContent? sender,
    DateTime? createdAt,
  }) {
    return ChatMessageContent(
      id: id ?? this.id,
      body: body ?? this.body,
      time: time ?? this.time,
      isFromMe: isFromMe ?? this.isFromMe,
      type: type ?? this.type,
      conversationId: conversationId ?? this.conversationId,
      sender: sender ?? this.sender,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  @override
  List<Object?> get props => [
    id,
    body,
    time,
    isFromMe,
    type,
    conversationId,
    sender,
    createdAt,
  ];
}

abstract final class ChatContent {
  static const List<ConversationContent> conversations = [
    ConversationContent(
      id: 1,
      name: 'أحمد محمد',
      property: 'شقة مدينة نصر',
      lastMessage: 'ممتاز، العنوان: شارع عباس العقاد...',
      time: '9:30 ص',
      unreadCount: 0,
      isVerified: true,
      isOnline: true,
    ),
    ConversationContent(
      id: 2,
      name: 'منى علي',
      property: 'ستوديو التجمع',
      lastMessage: 'متى تريد تعمل الزيارة؟',
      time: 'أمس',
      unreadCount: 2,
      isVerified: true,
      isOnline: false,
    ),
    ConversationContent(
      id: 3,
      name: 'كريم طارق',
      property: 'شقة المعادي',
      lastMessage: 'الشقة متاحة للعرض طول الأسبوع',
      time: 'الأثنين',
      unreadCount: 0,
      isVerified: false,
      isOnline: false,
    ),
  ];

  static const List<ConversationContent> searchConversations = [
    ConversationContent(
      id: 1,
      name: 'أحمد محمد',
      property: 'شقة مدينة نصر',
      lastMessage: 'ممتاز، العنوان: شارع عباس العقاد...',
      time: '9:30 ص',
      unreadCount: 0,
      isVerified: true,
      isOnline: true,
    ),
    ConversationContent(
      id: 4,
      name: 'أحمد طارق',
      property: 'ستوديو الزمالك',
      lastMessage: 'أحمد طارق: تفضل بأي استفسار...',
      time: 'أمس',
      unreadCount: 0,
      isVerified: true,
      isOnline: false,
    ),
  ];

  static const List<String> mentionedProperties = [
    'شقة مدينة نصر',
    'ستوديو الزمالك',
  ];

  static const List<ChatMessageContent> initialMessages = [
    ChatMessageContent(
      id: 1,
      body: 'أهلاً! الشقة لسه متاحة، تحب تحجز زيارة؟',
      time: '9:10 ص',
      isFromMe: false,
    ),
    ChatMessageContent(
      id: 2,
      body: 'أيوه عايز أزور يوم السبت الساعة 2م',
      time: '9:12 ص',
      isFromMe: true,
    ),
    ChatMessageContent(
      id: 3,
      body: 'تمام، هينفع معايا. هبعتلك تأكيد',
      time: '9:13 ص',
      isFromMe: false,
    ),
    ChatMessageContent(
      id: 4,
      body: 'شكراً جزيلاً',
      time: '9:14 ص',
      isFromMe: true,
    ),
  ];
}
