part of '../../imports.dart';

class VisitActions extends Equatable {
  const VisitActions({
    required this.canCancel,
    required this.canChat,
    required this.canReview,
    required this.canFindAlternative,
  });
  const VisitActions.initial()
    : canCancel = false,
      canChat = false,
      canReview = false,
      canFindAlternative = false;

  factory VisitActions.fromJson(Map<String, dynamic> json) => VisitActions(
    canCancel: json['can_cancel'] == true,
    canChat: json['can_chat'] == true,
    canReview: json['can_review'] == true,
    canFindAlternative: json['can_find_alternative'] == true,
  );
  final bool canCancel;
  final bool canChat;
  final bool canReview;
  final bool canFindAlternative;
  Map<String, dynamic> toJson() => {
    'can_cancel': canCancel,
    'can_chat': canChat,
    'can_review': canReview,
    'can_find_alternative': canFindAlternative,
  };
  VisitActions copyWith({
    bool? canCancel,
    bool? canChat,
    bool? canReview,
    bool? canFindAlternative,
  }) => VisitActions(
    canCancel: canCancel ?? this.canCancel,
    canChat: canChat ?? this.canChat,
    canReview: canReview ?? this.canReview,
    canFindAlternative: canFindAlternative ?? this.canFindAlternative,
  );
  @override
  List<Object?> get props => [
    canCancel,
    canChat,
    canReview,
    canFindAlternative,
  ];
}

Map<String, dynamic> _visitMap(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : const {};
