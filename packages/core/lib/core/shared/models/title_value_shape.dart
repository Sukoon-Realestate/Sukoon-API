import 'package:equatable/equatable.dart';

class TitleValueShape extends Equatable{
  final String title;
  final String value;

  const TitleValueShape({
    required this.title,
    required this.value,
  });

  factory TitleValueShape.initial() => const TitleValueShape(title: '', value: '');

  factory TitleValueShape.fromSingleLabel(String? label) => TitleValueShape(
      title: label ?? '',
      value: label ?? ''
  );

  factory TitleValueShape.fromJson(Map<String, dynamic> json) => TitleValueShape(
      title: json['title']??'',
      value: json['value']??''
  );

  Map<String, dynamic> toJson() => {
    'title' : title,
    'value' : value,
  };

  TitleValueShape copyWith({
    String? title,
    String? value,
  }) => TitleValueShape(title: title ?? this.title, value: value ?? this.value);

  @override
  List<Object?> get props => [
    title,
    value,
  ];
}