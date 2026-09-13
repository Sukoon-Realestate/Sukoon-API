import 'package:equatable/equatable.dart';

class NotificationSettingContent extends Equatable {
  const NotificationSettingContent({
    required this.id,
    required this.title,
    required this.description,
    required this.isEnabled,
    required this.canChange,
  });

  const NotificationSettingContent.initial({required this.id})
    : title = '',
      description = '',
      isEnabled = false,
      canChange = true;

  factory NotificationSettingContent.fromJson(Map<String, dynamic> json) {
    return NotificationSettingContent(
      id: json['key']?.toString() ?? json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      description: json['subtitle']?.toString() ?? '',
      isEnabled: _boolFromJson(json['value']),
      canChange: !json.containsKey('enabled') || _boolFromJson(json['enabled']),
    );
  }

  final String id;
  final String title;
  final String description;
  final bool isEnabled;
  final bool canChange;

  NotificationSettingContent copyWith({
    String? id,
    String? title,
    String? description,
    bool? isEnabled,
    bool? canChange,
  }) {
    return NotificationSettingContent(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      isEnabled: isEnabled ?? this.isEnabled,
      canChange: canChange ?? this.canChange,
    );
  }

  Map<String, dynamic> toJson() => {
    'key': id,
    'title': title,
    'subtitle': description,
    'value': isEnabled,
    'enabled': canChange,
  };

  @override
  List<Object?> get props => [id, title, description, isEnabled, canChange];
}

class NotificationSettingsContent extends Equatable {
  const NotificationSettingsContent({
    required this.id,
    required this.items,
    required this.footerNote,
  });

  const NotificationSettingsContent.initial()
    : id = '',
      items = const [
        NotificationSettingContent.initial(id: 'visit_notifications'),
        NotificationSettingContent.initial(id: 'owner_messages'),
        NotificationSettingContent.initial(id: 'property_updates'),
        NotificationSettingContent.initial(id: 'security_alerts'),
        NotificationSettingContent.initial(id: 'promotions_and_updates'),
      ],
      footerNote = '';

  factory NotificationSettingsContent.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> sections = _mapFromJson(json['sections']);
    final Map<String, dynamic> notificationSection = _mapFromJson(
      sections['notifications'],
    );
    final List<dynamic> rawItems =
        notificationSection['items'] as List? ?? const [];
    final List<NotificationSettingContent> parsedItems = rawItems
        .whereType<Map>()
        .map(
          (item) => NotificationSettingContent.fromJson(
            Map<String, dynamic>.from(item),
          ),
        )
        .where((item) => item.id.isNotEmpty)
        .toList(growable: false);

    const NotificationSettingsContent defaults =
        NotificationSettingsContent.initial();
    final List<NotificationSettingContent> items = parsedItems.isNotEmpty
        ? parsedItems
        : defaults.items
              .map(
                (item) =>
                    item.copyWith(isEnabled: _boolFromJson(json[item.id])),
              )
              .toList(growable: false);

    return NotificationSettingsContent(
      id: json['id']?.toString() ?? '',
      items: items,
      footerNote: notificationSection['footer_note']?.toString() ?? '',
    );
  }

  final String id;
  final List<NotificationSettingContent> items;
  final String footerNote;

  NotificationSettingsContent updateValue(String key, bool value) {
    return NotificationSettingsContent(
      id: id,
      items: items
          .map(
            (item) => item.id == key ? item.copyWith(isEnabled: value) : item,
          )
          .toList(growable: false),
      footerNote: footerNote,
    );
  }

  NotificationSettingsContent copyWith({
    String? id,
    List<NotificationSettingContent>? items,
    String? footerNote,
  }) {
    return NotificationSettingsContent(
      id: id ?? this.id,
      items: items ?? this.items,
      footerNote: footerNote ?? this.footerNote,
    );
  }

  NotificationSettingsContent mergeJson(Map<String, dynamic> json) {
    if (json.containsKey('sections')) {
      final NotificationSettingsContent parsed =
          NotificationSettingsContent.fromJson(json);
      return NotificationSettingsContent(
        id: parsed.id.isEmpty ? id : parsed.id,
        items: parsed.items,
        footerNote: parsed.footerNote.isEmpty ? footerNote : parsed.footerNote,
      );
    }

    NotificationSettingsContent merged = copyWith(id: json['id']?.toString());
    for (final NotificationSettingContent item in items) {
      if (json.containsKey(item.id)) {
        merged = merged.updateValue(item.id, _boolFromJson(json[item.id]));
      }
    }
    return merged;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    for (final item in items) item.id: item.isEnabled,
    'sections': {
      'notifications': {
        'items': items.map((item) => item.toJson()).toList(growable: false),
        'footer_note': footerNote,
      },
    },
  };

  @override
  List<Object?> get props => [id, items, footerNote];
}

Map<String, dynamic> _mapFromJson(Object? value) {
  if (value is! Map) return const {};
  return Map<String, dynamic>.from(value);
}

bool _boolFromJson(Object? value) {
  if (value is bool) return value;
  if (value is num) return value != 0;
  return value?.toString().toLowerCase() == 'true';
}
