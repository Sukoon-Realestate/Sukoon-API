enum AppNotificationIconKind {
  calendar('calendar'),
  checkCircle('check_circle'),
  cancel('cancel'),
  star('star'),
  chat('chat'),
  verified('verified'),
  eye('eye'),
  warning('warning'),
  bell('bell'),
  refresh('refresh'),
  shield('shield'),
  unknown('unknown');

  const AppNotificationIconKind(this.apiValue);

  final String apiValue;

  static AppNotificationIconKind fromApiValue(Object? value) {
    final String normalized = value?.toString().trim().toLowerCase() ?? '';
    return AppNotificationIconKind.values.firstWhere(
      (icon) => icon.apiValue == normalized,
      orElse: () => AppNotificationIconKind.unknown,
    );
  }
}
