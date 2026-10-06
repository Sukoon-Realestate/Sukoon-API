import 'package:equatable/equatable.dart';

class ActiveFilterContent extends Equatable {
  const ActiveFilterContent({required this.id, required this.label});

  const ActiveFilterContent.initial() : id = '', label = '';

  factory ActiveFilterContent.fromJson(Map<String, dynamic> json) {
    return ActiveFilterContent(
      id: json['id'] as String? ?? '',
      label: json['label'] as String? ?? '',
    );
  }

  final String id;
  final String label;

  Map<String, dynamic> toJson() => {'id': id, 'label': label};

  ActiveFilterContent copyWith({String? id, String? label}) {
    return ActiveFilterContent(id: id ?? this.id, label: label ?? this.label);
  }

  @override
  List<Object?> get props => [id, label];
}
