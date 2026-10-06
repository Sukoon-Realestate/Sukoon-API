import 'package:equatable/equatable.dart';
import '../premium_json.dart';
import 'promotion_option.dart';

/// Operational options for free tools. This model has no purchase allowances.
class FeatureConfiguration extends Equatable {
  const FeatureConfiguration({
    this.workspace = '',
    this.boostOptions = const [],
    this.alertCadences = const [],
  });
  const FeatureConfiguration.initial() : this();
  factory FeatureConfiguration.fromJson(Map<String, dynamic> json) =>
      FeatureConfiguration(
        workspace: premiumString(json['workspace']),
        boostOptions: premiumMaps(
          json['boost_options'],
        ).map(PromotionOption.fromJson).toList(growable: false),
        alertCadences:
            (json['alert_cadences'] is List
                    ? json['alert_cadences'] as List
                    : const [])
                .whereType<String>()
                .where((value) => value.isNotEmpty)
                .toSet()
                .toList(growable: false),
      );
  final String workspace;
  final List<PromotionOption> boostOptions;
  final List<String> alertCadences;
  Map<String, dynamic> toJson() => {
    'workspace': workspace,
    'boost_options': boostOptions.map((value) => value.toJson()).toList(),
    'alert_cadences': alertCadences,
  };
  FeatureConfiguration copyWith({
    String? workspace,
    List<PromotionOption>? boostOptions,
    List<String>? alertCadences,
  }) => FeatureConfiguration(
    workspace: workspace ?? this.workspace,
    boostOptions: boostOptions ?? this.boostOptions,
    alertCadences: alertCadences ?? this.alertCadences,
  );
  @override
  List<Object?> get props => [workspace, boostOptions, alertCadences];
}
