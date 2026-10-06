import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'lease_template.dart';

class LeaseConfiguration extends Equatable {
  const LeaseConfiguration({this.templates = const [], this.canCreate = false});
  const LeaseConfiguration.initial() : this();
  factory LeaseConfiguration.fromJson(Map<String, dynamic> json) =>
      LeaseConfiguration(
        templates: premiumMaps(
          json['templates'],
        ).map(LeaseTemplate.fromJson).toList(growable: false),
        canCreate: json['can_create'] == true,
      );
  final List<LeaseTemplate> templates;
  final bool canCreate;

  Map<String, dynamic> toJson() => {
    'templates': templates.map((item) => item.toJson()).toList(growable: false),
    'can_create': canCreate,
  };
  LeaseConfiguration copyWith({
    List<LeaseTemplate>? templates,
    bool? canCreate,
  }) => LeaseConfiguration(
    templates: templates ?? this.templates,
    canCreate: canCreate ?? this.canCreate,
  );
  @override
  List<Object?> get props => [templates, canCreate];
}
