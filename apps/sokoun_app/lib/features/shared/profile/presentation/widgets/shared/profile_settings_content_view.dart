part of '../../../imports.dart';

class ProfileSettingsContentView extends StatelessWidget {
  const ProfileSettingsContentView({
    super.key,
    required this.settings,
    required this.onChanged,
  });
  final ProfileSettingsContent settings;
  final void Function(ProfileSetting, bool) onChanged;
  @override
  Widget build(
    BuildContext context,
  ) => BlocBuilder<ProfileSettingUpdateCubit, AsyncState<ProfileSetting?>>(
    builder: (context, state) => ListView(
      padding: EdgeInsets.all(20.r),
      children: [
        for (final entry in settings.values.entries)
          ProfileSurfaceCard(
            child: SwitchListTile.adaptive(
              title: AppText(entry.key.label, style: AppTextStyles.regular14),
              value: entry.value,
              onChanged: state.isLoading
                  ? null
                  : (value) => onChanged(entry.key, value),
              secondary: state.isLoading && state.data == entry.key
                  ? SizedBox.square(
                      dimension: 20.r,
                      child: const CircularProgressIndicator(strokeWidth: 2),
                    )
                  : null,
            ),
          ),
      ],
    ),
  );
}
