import 'dart:io';
import '../../../../main_view/data/enums/app_workspace.dart';
import '../enums/support_topic.dart';

class SupportTicketBody {
  const SupportTicketBody({
    required this.workspace,
    required this.topic,
    required this.subject,
    required this.description,
    this.attachments = const [],
  });
  const SupportTicketBody.initial({required this.workspace})
    : topic = SupportTopic.visit,
      subject = '',
      description = '',
      attachments = const [];
  final AppWorkspace workspace;
  final SupportTopic topic;
  final String subject;
  final String description;
  final List<File> attachments;
  bool get hasChanges =>
      subject.trim().isNotEmpty ||
      description.trim().isNotEmpty ||
      attachments.isNotEmpty ||
      topic != SupportTopic.visit;
  Map<String, dynamic> toJson() => {
    'workspace': workspace.name,
    'category': topic.apiValue,
    'subject': subject.trim(),
    'description': description.trim(),
    if (attachments.isNotEmpty) 'attachments': List<File>.of(attachments),
  };
  SupportTicketBody copyWith({
    SupportTopic? topic,
    String? subject,
    String? description,
    List<File>? attachments,
  }) => SupportTicketBody(
    workspace: workspace,
    topic: topic ?? this.topic,
    subject: subject ?? this.subject,
    description: description ?? this.description,
    attachments: List.unmodifiable(attachments ?? this.attachments),
  );
}
