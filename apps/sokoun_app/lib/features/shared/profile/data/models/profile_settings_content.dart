part of '../../imports.dart';

class ProfileSettingsContent extends Equatable {
  const ProfileSettingsContent({required this.values});
  const ProfileSettingsContent.initial() : values = const {};
  factory ProfileSettingsContent.fromJson(Map<String, dynamic> json) =>
      ProfileSettingsContent(
        values: Map.unmodifiable({
          for (final setting in ProfileSetting.values)
            if (json[setting.apiKey] is bool)
              setting: json[setting.apiKey] as bool,
        }),
      );
  final Map<ProfileSetting, bool> values;
  Map<String, dynamic> toJson() => {
    for (final entry in values.entries) entry.key.apiKey: entry.value,
  };
  ProfileSettingsContent copyWith({Map<ProfileSetting, bool>? values}) =>
      ProfileSettingsContent(values: Map.unmodifiable(values ?? this.values));
  @override
  List<Object?> get props => [values];
}
