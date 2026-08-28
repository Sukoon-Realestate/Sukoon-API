import '../enums/notification_role.dart';

enum AppNotificationKind {
  visitAccepted,
  newProperty,
  accountVerification,
  rateVisit,
  ownerMessage,
  visitRequest,
  tenantMessage,
  propertyViews,
  propertyVerified,
  dailyVisibility,
}

class AppNotificationContent {
  const AppNotificationContent({
    required this.id,
    required this.kind,
    required this.title,
    required this.description,
    required this.time,
    required this.category,
    required this.isUnread,
    this.detailDescription,
    this.detailLabel,
    this.detailDate,
    this.detailLocation,
  });

  factory AppNotificationContent.initial() => const AppNotificationContent(
    id: '',
    kind: AppNotificationKind.visitAccepted,
    title: '',
    description: '',
    time: '',
    category: '',
    isUnread: false,
  );

  factory AppNotificationContent.fromJson(Map<String, dynamic> json) {
    return AppNotificationContent(
      id: json['id'] ?? '',
      kind: AppNotificationKind.values.firstWhere(
        (kind) => kind.name == json['kind'],
        orElse: () => AppNotificationKind.visitAccepted,
      ),
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      time: json['time'] ?? '',
      category: json['category'] ?? '',
      isUnread: json['is_unread'] ?? false,
      detailDescription: json['detail_description'],
      detailLabel: json['detail_label'],
      detailDate: json['detail_date'],
      detailLocation: json['detail_location'],
    );
  }

  final String id;
  final AppNotificationKind kind;
  final String title;
  final String description;
  final String time;
  final String category;
  final bool isUnread;
  final String? detailDescription;
  final String? detailLabel;
  final String? detailDate;
  final String? detailLocation;

  bool get hasDetailCard =>
      detailLabel != null || detailDate != null || detailLocation != null;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'kind': kind.name,
      'title': title,
      'description': description,
      'time': time,
      'category': category,
      'is_unread': isUnread,
      'detail_description': detailDescription,
      'detail_label': detailLabel,
      'detail_date': detailDate,
      'detail_location': detailLocation,
    };
  }

  AppNotificationContent copyWith({
    String? id,
    AppNotificationKind? kind,
    String? title,
    String? description,
    String? time,
    String? category,
    bool? isUnread,
    String? detailDescription,
    String? detailLabel,
    String? detailDate,
    String? detailLocation,
  }) {
    return AppNotificationContent(
      id: id ?? this.id,
      kind: kind ?? this.kind,
      title: title ?? this.title,
      description: description ?? this.description,
      time: time ?? this.time,
      category: category ?? this.category,
      isUnread: isUnread ?? this.isUnread,
      detailDescription: detailDescription ?? this.detailDescription,
      detailLabel: detailLabel ?? this.detailLabel,
      detailDate: detailDate ?? this.detailDate,
      detailLocation: detailLocation ?? this.detailLocation,
    );
  }
}

abstract final class NotificationsContent {
  static List<AppNotificationContent> forRole(NotificationRole role) {
    return role.isOwner ? ownerNotifications : tenantNotifications;
  }

  static const List<AppNotificationContent> tenantNotifications = [
    AppNotificationContent(
      id: 'tenant-visit-accepted',
      kind: AppNotificationKind.visitAccepted,
      title: 'تم قبول طلب زيارتك',
      description: 'المالك أحمد محمد وافق على موعد الزيارة',
      time: 'منذ 5 دقائق',
      category: 'حجز زيارة',
      isUnread: true,
      detailDescription:
          'وافق المالك أحمد محمد على موعد الزيارة. يُرجى الحضور في الوقت المحدد للاطلاع على الشقة.',
      detailLabel: 'تفاصيل الموعد',
      detailDate: 'الثلاثاء 14 يناير · 3:00 م',
      detailLocation: 'مدينة نصر — شارع عباس العقاد',
    ),
    AppNotificationContent(
      id: 'tenant-new-property',
      kind: AppNotificationKind.newProperty,
      title: 'عقار جديد في منطقتك',
      description: 'شقة مفروشة 3 غرف — مدينة نصر 11,500 ج.م/شهر',
      time: 'منذ ساعة',
      category: 'عقار جديد',
      isUnread: true,
    ),
    AppNotificationContent(
      id: 'tenant-verification',
      kind: AppNotificationKind.accountVerification,
      title: 'أكمل توثيق حسابك',
      description: 'وثّق هويتك عشان تستخدم الشات بدون قيود',
      time: 'منذ يومين',
      category: 'توثيق الحساب',
      isUnread: false,
    ),
    AppNotificationContent(
      id: 'tenant-rate-visit',
      kind: AppNotificationKind.rateVisit,
      title: 'قيّم تجربتك بعد الزيارة',
      description: 'شقة مدينة نصر — اضغط لتقديم تقييمك',
      time: 'منذ 3 أيام',
      category: 'تقييم الزيارة',
      isUnread: false,
    ),
    AppNotificationContent(
      id: 'tenant-owner-message',
      kind: AppNotificationKind.ownerMessage,
      title: 'رسالة جديدة من المالك',
      description: 'أحمد محمد: الشقة لسه متاحة، هل تريد معلومات أكتر؟',
      time: 'منذ أسبوع',
      category: 'رسالة جديدة',
      isUnread: false,
    ),
  ];

  static const List<AppNotificationContent> ownerNotifications = [
    AppNotificationContent(
      id: 'owner-visit-request',
      kind: AppNotificationKind.visitRequest,
      title: 'طلب زيارة جديد!',
      description: 'سارة أحمد تطلب زيارة شقة مدينة نصر — النهارده 3م',
      time: 'منذ 5 دقائق',
      category: 'طلب زيارة',
      isUnread: true,
      detailDescription:
          'طلبت سارة أحمد زيارة شقة مدينة نصر. راجع الموعد وقم بقبول الطلب أو اقتراح وقت آخر.',
      detailLabel: 'تفاصيل الطلب',
      detailDate: 'النهارده · 3:00 م',
      detailLocation: 'شقة مدينة نصر — شارع عباس العقاد',
    ),
    AppNotificationContent(
      id: 'owner-tenant-message',
      kind: AppNotificationKind.tenantMessage,
      title: 'رسالة جديدة من مستأجر',
      description: 'محمد علي: هل الشقة لسه متاحة؟',
      time: 'منذ ساعة',
      category: 'رسالة جديدة',
      isUnread: true,
    ),
    AppNotificationContent(
      id: 'owner-property-views',
      kind: AppNotificationKind.propertyViews,
      title: 'شقتك حصلت على 50 مشاهدة',
      description: 'شقة مفروشة، مدينة نصر — أداء متميز هذا الأسبوع',
      time: 'اليوم 9 ص',
      category: 'أداء العقار',
      isUnread: false,
    ),
    AppNotificationContent(
      id: 'owner-property-verified',
      kind: AppNotificationKind.propertyVerified,
      title: 'عقارك تم توثيقه',
      description: 'ستوديو، التجمع الخامس — يظهر الآن في نتائج البحث',
      time: 'أمس',
      category: 'توثيق العقار',
      isUnread: false,
    ),
    AppNotificationContent(
      id: 'owner-daily-visibility',
      kind: AppNotificationKind.dailyVisibility,
      title: 'تحديث الظهور اليومي',
      description: 'حدّث عقاراتك يومياً للحفاظ على ترتيبها في البحث',
      time: 'منذ يومين',
      category: 'تحديث العقار',
      isUnread: false,
    ),
  ];
}
