class NotificationSettingContent {
  const NotificationSettingContent({
    required this.id,
    required this.title,
    required this.description,
    required this.isEnabled,
  });

  final String id;
  final String title;
  final String description;
  final bool isEnabled;

  NotificationSettingContent copyWith({
    String? id,
    String? title,
    String? description,
    bool? isEnabled,
  }) {
    return NotificationSettingContent(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      isEnabled: isEnabled ?? this.isEnabled,
    );
  }
}
