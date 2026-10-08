import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:equatable/equatable.dart';

class NotificationPayloadContent extends Equatable {
  const NotificationPayloadContent({
    this.targetId = '',
    this.workspace = '',
    this.offerId = '',
    this.rentalSelection,
    required this.visitId,
    required this.propertyId,
    required this.chatId,
    required this.messageId,
    required this.senderId,
    required this.promoUrl,
    required this.actionType,
    required this.actionLabel,
    required this.visitDate,
    required this.visitTime,
    required this.tenantName,
    required this.senderName,
    required this.viewsCount,
    required this.appointmentDate,
    required this.appointmentTime,
    required this.address,
  });

  const NotificationPayloadContent.initial()
    : targetId = '',
      workspace = '',
      offerId = '',
      rentalSelection = null,
      visitId = '',
      propertyId = '',
      chatId = '',
      messageId = '',
      senderId = '',
      promoUrl = '',
      actionType = '',
      actionLabel = '',
      visitDate = '',
      visitTime = '',
      tenantName = '',
      senderName = '',
      viewsCount = 0,
      appointmentDate = '',
      appointmentTime = '',
      address = '';

  factory NotificationPayloadContent.fromJson(Map<String, dynamic> json) {
    return NotificationPayloadContent(
      targetId: json['target_id']?.toString() ?? '',
      workspace: json['workspace']?.toString() ?? '',
      offerId: json['offer_id']?.toString() ?? '',
      rentalSelection: RentalSelection.fromRecord(json),
      visitId: json['visit_id']?.toString() ?? '',
      propertyId: json['property_id']?.toString() ?? '',
      chatId:
          json['conversation_id']?.toString() ??
          json['chat_id']?.toString() ??
          '',
      messageId: json['message_id']?.toString() ?? '',
      senderId: json['sender_id']?.toString() ?? '',
      promoUrl: json['promo_url']?.toString() ?? '',
      actionType: json['action_type']?.toString() ?? '',
      actionLabel: json['action_label']?.toString() ?? '',
      visitDate: json['visit_date']?.toString() ?? '',
      visitTime: json['visit_time']?.toString() ?? '',
      tenantName: json['tenant_name']?.toString() ?? '',
      senderName: json['sender_name']?.toString() ?? '',
      viewsCount:
          (json['views_count'] as num?)?.toInt() ??
          int.tryParse('${json['views_count'] ?? ''}') ??
          0,
      appointmentDate: json['appointment_date']?.toString() ?? '',
      appointmentTime: json['appointment_time']?.toString() ?? '',
      address: json['address']?.toString() ?? '',
    );
  }

  final String offerId;
  final String targetId;
  final String workspace;
  final RentalSelection? rentalSelection;
  final String visitId;
  final String propertyId;
  final String chatId;
  final String messageId;
  final String senderId;
  final String promoUrl;
  final String actionType;
  final String actionLabel;
  final String visitDate;
  final String visitTime;
  final String tenantName;
  final String senderName;
  final int viewsCount;
  final String appointmentDate;
  final String appointmentTime;
  final String address;

  String get appointmentDateTime => [
    appointmentDate,
    appointmentTime,
  ].where((value) => value.trim().isNotEmpty).join(' · ');

  Map<String, dynamic> toJson() => {
    if (targetId.isNotEmpty) 'target_id': targetId,
    if (workspace.isNotEmpty) 'workspace': workspace,
    if (offerId.isNotEmpty) 'offer_id': offerId,
    if (rentalSelection != null) 'offer_snapshot': rentalSelection!.toJson(),
    if (visitId.isNotEmpty) 'visit_id': visitId,
    if (propertyId.isNotEmpty) 'property_id': propertyId,
    if (chatId.isNotEmpty) 'conversation_id': chatId,
    if (messageId.isNotEmpty) 'message_id': messageId,
    if (senderId.isNotEmpty) 'sender_id': senderId,
    if (promoUrl.isNotEmpty) 'promo_url': promoUrl,
    if (actionType.isNotEmpty) 'action_type': actionType,
    if (actionLabel.isNotEmpty) 'action_label': actionLabel,
    if (visitDate.isNotEmpty) 'visit_date': visitDate,
    if (visitTime.isNotEmpty) 'visit_time': visitTime,
    if (tenantName.isNotEmpty) 'tenant_name': tenantName,
    if (senderName.isNotEmpty) 'sender_name': senderName,
    if (viewsCount > 0) 'views_count': viewsCount,
    if (appointmentDate.isNotEmpty) 'appointment_date': appointmentDate,
    if (appointmentTime.isNotEmpty) 'appointment_time': appointmentTime,
    if (address.isNotEmpty) 'address': address,
  };

  NotificationPayloadContent copyWith({
    String? targetId,
    String? workspace,
    String? offerId,
    RentalSelection? rentalSelection,
    String? visitId,
    String? propertyId,
    String? chatId,
    String? messageId,
    String? senderId,
    String? promoUrl,
    String? actionType,
    String? actionLabel,
    String? visitDate,
    String? visitTime,
    String? tenantName,
    String? senderName,
    int? viewsCount,
    String? appointmentDate,
    String? appointmentTime,
    String? address,
  }) {
    return NotificationPayloadContent(
      targetId: targetId ?? this.targetId,
      workspace: workspace ?? this.workspace,
      offerId: offerId ?? this.offerId,
      rentalSelection: rentalSelection ?? this.rentalSelection,
      visitId: visitId ?? this.visitId,
      propertyId: propertyId ?? this.propertyId,
      chatId: chatId ?? this.chatId,
      messageId: messageId ?? this.messageId,
      senderId: senderId ?? this.senderId,
      promoUrl: promoUrl ?? this.promoUrl,
      actionType: actionType ?? this.actionType,
      actionLabel: actionLabel ?? this.actionLabel,
      visitDate: visitDate ?? this.visitDate,
      visitTime: visitTime ?? this.visitTime,
      tenantName: tenantName ?? this.tenantName,
      senderName: senderName ?? this.senderName,
      viewsCount: viewsCount ?? this.viewsCount,
      appointmentDate: appointmentDate ?? this.appointmentDate,
      appointmentTime: appointmentTime ?? this.appointmentTime,
      address: address ?? this.address,
    );
  }

  @override
  List<Object?> get props => [
    targetId,
    workspace,
    offerId,
    rentalSelection,
    visitId,
    propertyId,
    chatId,
    messageId,
    senderId,
    promoUrl,
    actionType,
    actionLabel,
    visitDate,
    visitTime,
    tenantName,
    senderName,
    viewsCount,
    appointmentDate,
    appointmentTime,
    address,
  ];
}
