part of '../../imports.dart';

class ProfilePrivacyScreen extends StatefulWidget {
  const ProfilePrivacyScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  State<ProfilePrivacyScreen> createState() => _ProfilePrivacyScreenState();
}

class _ProfilePrivacyScreenState extends State<ProfilePrivacyScreen> {
  late final ProfileSettingsCubit _settings;
  late final ProfileSettingUpdateCubit _update;
  late final Future<void> _loadRequest;
  @override
  void initState() {
    super.initState();
    _settings = ProfileSettingsCubit();
    _update = ProfileSettingUpdateCubit();
    _loadRequest = _settings.load();
  }

  @override
  void dispose() {
    _settings.close();
    _update.close();
    super.dispose();
  }

  Future<void> _retry() async {
    await _loadRequest;
    if (mounted) await _settings.load();
  }

  Future<void> _change(ProfileSetting setting, bool value) async {
    final bool baseline = _settings.data.values[setting] ?? false;
    _settings.apply(setting, value);
    await _update.save(setting, value, baseline: baseline);
    if (mounted) {
      _settings.apply(setting, _update.desiredValue(setting, baseline));
    }
  }

  @override
  Widget build(BuildContext context) => MultiBlocProvider(
    providers: [
      BlocProvider.value(value: _settings),
      BlocProvider.value(value: _update),
    ],
    child: AppScaffold(
      title: LocaleKeys.settingsPrivacyOptions,
      body: SafeArea(
        child:
            StatusBuilder<
              ProfileSettingsCubit,
              ProfileSettingsContent
            >.withShimmer(
              initialDataForShimmer: const ProfileSettingsContent.initial(),
              onRetry: _retry,
              shimmerBuilder: (_) => ProfilePrivacyContentView(
                settings: const ProfileSettingsContent(
                  values: {
                    ProfileSetting.shareLocation: false,
                    ProfileSetting.showProfile: false,
                  },
                ),
                workspace: widget.workspace,
                onChanged: _change,
              ),
              builder: (settings) => ProfilePrivacyContentView(
                settings: settings,
                workspace: widget.workspace,
                onChanged: _change,
              ),
            ),
      ),
    ),
  );
}
