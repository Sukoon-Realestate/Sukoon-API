enum SupportTicketState {
  open('open'),
  inProgress('in_progress'),
  resolved('resolved'),
  closed('closed'),
  unknown('unknown');

  const SupportTicketState(this.code);
  final String code;

  static SupportTicketState fromJson(Object? value) => values.firstWhere(
    (status) => status.code == value,
    orElse: () => unknown,
  );

  bool get canReply => this == open || this == inProgress;
  bool get isResolved => this == resolved || this == closed;
}
