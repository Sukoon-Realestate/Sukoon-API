import '../private_recovery_data.dart';
import '../recovery_scope.dart';

/// Text and stable selection IDs only. Private attachments require reselection.
class TextFormDraft {
  const TextFormDraft(this.fields, {this.submissionUnconfirmed = false});
  const TextFormDraft.initial()
    : fields = const {},
      submissionUnconfirmed = false;
  final Map<String, String> fields;
  final bool submissionUnconfirmed;
  String operator [](String field) => fields[field] ?? '';
  factory TextFormDraft.fromJson(Map<String, dynamic> json) => TextFormDraft(
    Map<String, String>.from(json['fields'] as Map? ?? const {}),
    submissionUnconfirmed: json['submission_unconfirmed'] == true,
  );
  Map<String, dynamic> toJson() => {
    'fields': fields,
    'submission_unconfirmed': submissionUnconfirmed,
  };
  static PrivateDraftStore<TextFormDraft> store({
    required String flow,
    String entityId = '',
    String workspace = '',
  }) => PrivateDraftStore(
    scope: () => RecoveryScope.current(
      flow: flow,
      entityId: entityId,
      workspace: workspace,
    ),
    encode: (value) => value.toJson(),
    decode: TextFormDraft.fromJson,
  );
}
