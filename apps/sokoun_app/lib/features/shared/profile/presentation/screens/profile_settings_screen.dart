part of '../../imports.dart';

class ProfileSettingsScreen extends StatefulWidget {
  const ProfileSettingsScreen({super.key});
  @override
  State<ProfileSettingsScreen> createState() => _ProfileSettingsScreenState();
}

class _ProfileSettingsScreenState extends State<ProfileSettingsScreen> {
  late final ProfileSettingsCubit _settings;
  late final ProfileSettingUpdateCubit _update;
  @override
  void initState() {
    super.initState();
    _settings = ProfileSettingsCubit();
    _update = ProfileSettingUpdateCubit();
    _settings.load();
  }

  @override
  void dispose() {
    _settings.close();
    _update.close();
    super.dispose();
  }

  Future<void> _change(ProfileSetting setting, bool value) async {
    if (await _update.save(setting, value) && mounted) {
      _settings.apply(setting, value);
    }
  }

  @override
  Widget build(BuildContext context) => MultiBlocProvider(
    providers: [
      BlocProvider.value(value: _settings),
      BlocProvider.value(value: _update),
    ],
    child: AppScaffold(
      title: LocaleKeys.profileSettingsTitle,
      showBackButton: true,
      body: SafeArea(
        child:
            StatusBuilder<
              ProfileSettingsCubit,
              ProfileSettingsContent
            >.withShimmer(
              initialDataForShimmer: const ProfileSettingsContent.initial(),
              onRetry: _settings.load,
              shimmerBuilder: (_) => ProfileSettingsContentView(
                settings: ProfileSettingsContent(
                  values: {for (final s in ProfileSetting.values) s: false},
                ),
                onChanged: _change,
              ),
              builder: (settings) => settings.values.isEmpty
                  ? const ProfileSettingsEmptyState()
                  : ProfileSettingsContentView(
                      settings: settings,
                      onChanged: _change,
                    ),
            ),
      ),
    ),
  );
}
