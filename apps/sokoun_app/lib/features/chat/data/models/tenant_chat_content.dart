class TenantConversationContent {
  const TenantConversationContent({
    required this.id,
    required this.name,
    required this.property,
    required this.lastMessage,
    required this.time,
    required this.unreadCount,
    required this.isVerified,
    required this.isOnline,
  });

  factory TenantConversationContent.initial() =>
      const TenantConversationContent(
        id: 0,
        name: '',
        property: '',
        lastMessage: '',
        time: '',
        unreadCount: 0,
        isVerified: false,
        isOnline: false,
      );

  factory TenantConversationContent.fromJson(Map<String, dynamic> json) {
    return TenantConversationContent(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      property: json['property'] ?? '',
      lastMessage: json['last_message'] ?? '',
      time: json['time'] ?? '',
      unreadCount: json['unread_count'] ?? 0,
      isVerified: json['is_verified'] ?? false,
      isOnline: json['is_online'] ?? false,
    );
  }

  final int id;
  final String name;
  final String property;
  final String lastMessage;
  final String time;
  final int unreadCount;
  final bool isVerified;
  final bool isOnline;

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
      'name': name,
      'property': property,
      'last_message': lastMessage,
      'time': time,
      'unread_count': unreadCount,
      'is_verified': isVerified,
      'is_online': isOnline,
    };
  }

  TenantConversationContent copyWith({
    int? id,
    String? name,
    String? property,
    String? lastMessage,
    String? time,
    int? unreadCount,
    bool? isVerified,
    bool? isOnline,
  }) {
    return TenantConversationContent(
      id: id ?? this.id,
      name: name ?? this.name,
      property: property ?? this.property,
      lastMessage: lastMessage ?? this.lastMessage,
      time: time ?? this.time,
      unreadCount: unreadCount ?? this.unreadCount,
      isVerified: isVerified ?? this.isVerified,
      isOnline: isOnline ?? this.isOnline,
    );
  }
}

class TenantChatMessageContent {
  const TenantChatMessageContent({
    required this.id,
    required this.body,
    required this.time,
    required this.isFromMe,
    this.type = 'text',
  });

  factory TenantChatMessageContent.initial() => const TenantChatMessageContent(
    id: 0,
    body: '',
    time: '',
    isFromMe: false,
  );

  factory TenantChatMessageContent.fromJson(Map<String, dynamic> json) {
    return TenantChatMessageContent(
      id: json['id'] ?? 0,
      body: json['body'] ?? '',
      time: json['time'] ?? '',
      isFromMe: json['is_from_me'] ?? false,
      type: json['type'] ?? 'text',
    );
  }

  final int id;
  final String body;
  final String time;
  final bool isFromMe;
  final String type;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'body': body,
      'time': time,
      'is_from_me': isFromMe,
      'type': type,
    };
  }

  TenantChatMessageContent copyWith({
    int? id,
    String? body,
    String? time,
    bool? isFromMe,
    String? type,
  }) {
    return TenantChatMessageContent(
      id: id ?? this.id,
      body: body ?? this.body,
      time: time ?? this.time,
      isFromMe: isFromMe ?? this.isFromMe,
      type: type ?? this.type,
    );
  }
}

abstract final class TenantChatContent {
  static const List<TenantConversationContent> conversations = [
    TenantConversationContent(
      id: 1,
      name: 'أحمد محمد',
      property: 'شقة مدينة نصر',
      lastMessage: 'ممتاز، العنوان: شارع عباس العقاد...',
      time: '9:30 ص',
      unreadCount: 0,
      isVerified: true,
      isOnline: true,
    ),
    TenantConversationContent(
      id: 2,
      name: 'منى علي',
      property: 'ستوديو التجمع',
      lastMessage: 'متى تريد تعمل الزيارة؟',
      time: 'أمس',
      unreadCount: 2,
      isVerified: true,
      isOnline: false,
    ),
    TenantConversationContent(
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

  static const List<TenantConversationContent> searchConversations = [
    TenantConversationContent(
      id: 1,
      name: 'أحمد محمد',
      property: 'شقة مدينة نصر',
      lastMessage: 'ممتاز، العنوان: شارع عباس العقاد...',
      time: '9:30 ص',
      unreadCount: 0,
      isVerified: true,
      isOnline: true,
    ),
    TenantConversationContent(
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

  static const List<TenantChatMessageContent> initialMessages = [
    TenantChatMessageContent(
      id: 1,
      body: 'أهلاً! الشقة لسه متاحة، تحب تحجز زيارة؟',
      time: '9:10 ص',
      isFromMe: false,
    ),
    TenantChatMessageContent(
      id: 2,
      body: 'أيوه عايز أزور يوم السبت الساعة 2م',
      time: '9:12 ص',
      isFromMe: true,
    ),
    TenantChatMessageContent(
      id: 3,
      body: 'تمام، هينفع معايا. هبعتلك تأكيد',
      time: '9:13 ص',
      isFromMe: false,
    ),
    TenantChatMessageContent(
      id: 4,
      body: 'شكراً جزيلاً',
      time: '9:14 ص',
      isFromMe: true,
    ),
  ];
}
