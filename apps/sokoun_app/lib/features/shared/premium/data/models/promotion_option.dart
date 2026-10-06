import 'package:equatable/equatable.dart';
import '../premium_json.dart';

class PromotionOption extends Equatable {
  const PromotionOption({this.id = '', this.title = '', this.durationDays = 0});
  const PromotionOption.initial() : this();
  factory PromotionOption.fromJson(Map<String, dynamic> json) =>
      PromotionOption(
        id: premiumString(json['id']),
        title: premiumString(json['title']),
        durationDays: premiumInt(json['duration_days']) ?? 0,
      );
  final String id;
  final String title;
  final int durationDays;
  bool get isValid => id.isNotEmpty && durationDays > 0;
  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'duration_days': durationDays,
  };
  PromotionOption copyWith({String? id, String? title, int? durationDays}) =>
      PromotionOption(
        id: id ?? this.id,
        title: title ?? this.title,
        durationDays: durationDays ?? this.durationDays,
      );
  @override
  List<Object?> get props => [id, title, durationDays];
}
