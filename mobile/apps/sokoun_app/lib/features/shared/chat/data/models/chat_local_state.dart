import 'package:equatable/equatable.dart';

class SavedChatMessage extends Equatable {
  const SavedChatMessage({required this.id, required this.content});
  const SavedChatMessage.initial() : id = '', content = '';
  factory SavedChatMessage.fromJson(Map<String, dynamic> json) =>
      SavedChatMessage(
        id: json['id'] as String? ?? '',
        content: json['content'] as String? ?? '',
      );
  final String id;
  final String content;
  Map<String, dynamic> toJson() => {'id': id, 'content': content};
  SavedChatMessage copyWith({String? id, String? content}) =>
      SavedChatMessage(id: id ?? this.id, content: content ?? this.content);
  @override
  List<Object?> get props => [id, content];
}

class ChatLocalState extends Equatable {
  const ChatLocalState({this.draft = '', this.messages = const []});
  const ChatLocalState.initial() : draft = '', messages = const [];
  factory ChatLocalState.fromJson(Map<String, dynamic> json) => ChatLocalState(
    draft: json['draft'] as String? ?? '',
    messages: (json['messages'] as List? ?? const [])
        .whereType<Map>()
        .map(
          (value) =>
              SavedChatMessage.fromJson(Map<String, dynamic>.from(value)),
        )
        .where((message) => message.id.isNotEmpty && message.content.isNotEmpty)
        .toList(growable: false),
  );
  final String draft;
  final List<SavedChatMessage> messages;
  Map<String, dynamic> toJson() => {
    'draft': draft,
    'messages': messages.map((message) => message.toJson()).toList(),
  };
  ChatLocalState copyWith({String? draft, List<SavedChatMessage>? messages}) =>
      ChatLocalState(
        draft: draft ?? this.draft,
        messages: messages ?? this.messages,
      );
  @override
  List<Object?> get props => [draft, messages];
}
