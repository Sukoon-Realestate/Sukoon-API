import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

class LeaseTenant extends Equatable {
  const LeaseTenant({this.id = '', this.displayName = ''});
  const LeaseTenant.initial() : this();
  factory LeaseTenant.fromJson(Map<String, dynamic> json) => LeaseTenant(
    id: premiumString(json['id']),
    displayName: premiumString(json['display_name']),
  );
  final String id;
  final String displayName;
  Map<String, dynamic> toJson() => {'id': id, 'display_name': displayName};
  LeaseTenant copyWith({String? id, String? displayName}) => LeaseTenant(
    id: id ?? this.id,
    displayName: displayName ?? this.displayName,
  );
  @override
  List<Object?> get props => [id, displayName];
}
