import 'package:equatable/equatable.dart';

import '../../../../main_view/data/enums/app_workspace.dart';
import '../../../../main_view/data/models/workspace_counts.dart';

class UnreadCounts extends Equatable {
  const UnreadCounts({
    required this.tenant,
    required this.owner,
    required this.chatCount,
    required this.notificationsCount,
  });

  const UnreadCounts.initial()
    : tenant = const WorkspaceCounts.initial(),
      owner = const WorkspaceCounts.initial(),
      chatCount = 0,
      notificationsCount = 0;

  factory UnreadCounts.fromJson(
    Map<String, dynamic> json, {
    AppWorkspace workspace = AppWorkspace.tenant,
  }) {
    final bool isCachedSnapshot = json['tenant'] is Map;
    return UnreadCounts(
      tenant: isCachedSnapshot
          ? WorkspaceCounts.fromJson(Map<String, dynamic>.from(json['tenant']))
          : workspace.isTenant
          ? WorkspaceCounts.fromJson(json)
          : const WorkspaceCounts.initial(),
      owner: isCachedSnapshot
          ? WorkspaceCounts.fromJson(Map<String, dynamic>.from(json['owner']))
          : workspace.isOwner
          ? WorkspaceCounts.fromJson(json)
          : const WorkspaceCounts.initial(),
      chatCount: _count(json['unread_chat_messages_count']),
      notificationsCount: _count(json['unread_notifications_count']),
    );
  }

  final WorkspaceCounts tenant;
  final WorkspaceCounts owner;
  final int chatCount;
  final int notificationsCount;

  WorkspaceCounts forWorkspace(AppWorkspace workspace) =>
      workspace.isOwner ? owner : tenant;

  Map<String, dynamic> toJson() => {
    'tenant': tenant.toJson(),
    'owner': owner.toJson(),
    'unread_chat_messages_count': chatCount,
    'unread_notifications_count': notificationsCount,
  };

  UnreadCounts copyWith({
    WorkspaceCounts? tenant,
    WorkspaceCounts? owner,
    int? chatCount,
    int? notificationsCount,
  }) => UnreadCounts(
    tenant: tenant ?? this.tenant,
    owner: owner ?? this.owner,
    chatCount: chatCount ?? this.chatCount,
    notificationsCount: notificationsCount ?? this.notificationsCount,
  );

  static int _count(Object? value) =>
      value is num ? value.toInt() : int.tryParse(value?.toString() ?? '') ?? 0;

  @override
  List<Object?> get props => [tenant, owner, chatCount, notificationsCount];
}
