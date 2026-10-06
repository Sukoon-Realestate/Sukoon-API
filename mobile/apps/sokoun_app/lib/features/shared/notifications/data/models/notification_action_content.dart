import 'package:equatable/equatable.dart';

class NotificationActionContent extends Equatable {
  const NotificationActionContent({
    required this.label,
    required this.actionType,
    required this.targetId,
  });

  const NotificationActionContent.initial()
    : label = '',
      actionType = '',
      targetId = '';

  factory NotificationActionContent.fromJson(Map<String, dynamic> json) {
    return NotificationActionContent(
      label: json['label']?.toString() ?? '',
      actionType: json['action_type']?.toString() ?? '',
      targetId: json['target_id']?.toString() ?? '',
    );
  }

  final String label;
  final String actionType;
  final String targetId;

  Map<String, dynamic> toJson() => {
    'label': label,
    'action_type': actionType,
    'target_id': targetId,
  };

  NotificationActionContent copyWith({
    String? label,
    String? actionType,
    String? targetId,
  }) {
    return NotificationActionContent(
      label: label ?? this.label,
      actionType: actionType ?? this.actionType,
      targetId: targetId ?? this.targetId,
    );
  }

  @override
  List<Object?> get props => [label, actionType, targetId];
}

class NotificationActionsContent extends Equatable {
  const NotificationActionsContent({this.primary, this.secondary});

  const NotificationActionsContent.initial() : primary = null, secondary = null;

  factory NotificationActionsContent.fromJson(Map<String, dynamic> json) {
    return NotificationActionsContent(
      primary: _actionFromJson(json['primary']),
      secondary: _actionFromJson(json['secondary']),
    );
  }

  final NotificationActionContent? primary;
  final NotificationActionContent? secondary;

  Map<String, dynamic> toJson() => {
    if (primary != null) 'primary': primary!.toJson(),
    if (secondary != null) 'secondary': secondary!.toJson(),
  };

  NotificationActionsContent copyWith({
    NotificationActionContent? primary,
    NotificationActionContent? secondary,
  }) {
    return NotificationActionsContent(
      primary: primary ?? this.primary,
      secondary: secondary ?? this.secondary,
    );
  }

  @override
  List<Object?> get props => [primary, secondary];
}

NotificationActionContent? _actionFromJson(Object? value) {
  if (value is! Map) return null;
  return NotificationActionContent.fromJson(Map<String, dynamic>.from(value));
}
