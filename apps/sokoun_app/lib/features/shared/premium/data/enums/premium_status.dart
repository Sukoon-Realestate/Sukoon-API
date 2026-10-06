import 'package:melos_core/config/language/locale_keys.g.dart';

enum PremiumStatus {
  unknown,
  draft,
  pending,
  active,
  paused,
  completed,
  cancelled,
  expired,
  failed,
  signed,
  due,
  paid,
  overdue;

  static PremiumStatus fromValue(Object? value) =>
      values.where((status) => status.name == value).firstOrNull ?? unknown;
  bool get isActive => this == active;
  bool get isPayable => this == due || this == overdue;
  bool get isSignable => this == draft || this == pending;
  bool get isPaid => this == paid;
  bool get isDraft => this == draft;
  bool get isPending => this == pending;
  bool get isCancelled => this == cancelled;
  bool get isPaused => this == paused;
  String get label => switch (this) {
    unknown => LocaleKeys.paidUnknownStatus,
    draft => LocaleKeys.paidDraft,
    pending => LocaleKeys.paidPending,
    active => LocaleKeys.paidActive,
    paused => LocaleKeys.paidPaused,
    completed => LocaleKeys.paidCompleted,
    cancelled => LocaleKeys.paidCancelled,
    expired => LocaleKeys.paidExpired,
    failed => LocaleKeys.paidFailed,
    signed => LocaleKeys.paidSigned,
    due => LocaleKeys.paidDue,
    paid => LocaleKeys.paidPaid,
    overdue => LocaleKeys.paidOverdue,
  };
}
