part of '../../../imports.dart';

class ProfilePrivacyContentView extends StatelessWidget {
  const ProfilePrivacyContentView({
    super.key,
    required this.settings,
    required this.workspace,
    required this.onChanged,
  });
  final ProfileSettingsContent settings;
  final AppWorkspace workspace;
  final void Function(ProfileSetting, bool) onChanged;
  @override
  Widget build(BuildContext context) =>
      BlocBuilder<ProfileSettingUpdateCubit, AsyncState<ProfileSetting?>>(
        builder: (context, state) {
          final Iterable<MapEntry<ProfileSetting, bool>> values = settings
              .values
              .entries
              .where(
                (entry) =>
                    entry.key == ProfileSetting.shareLocation ||
                    entry.key == ProfileSetting.showProfile,
              );
          return ListView(
            padding: EdgeInsets.all(20.r),
            children: [
              ProfileVerificationBanner(
                title: LocaleKeys.settingsPhonePrivacyTitle,
                description: LocaleKeys.settingsPhonePrivacyDescription,
                isPrivacy: true,
              ),
              18.szH,
              if (values.isEmpty) const ProfileSettingsEmptyState(),
              for (final entry in values)
                ProfileSurfaceCard(
                  child: SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: AppText(
                      entry.key.label,
                      style: AppTextStyles.bold14,
                    ),
                    subtitle: AppText(
                      entry.key == ProfileSetting.shareLocation
                          ? LocaleKeys.settingsLocationDescription
                          : LocaleKeys.settingsSearchProfileDescription,
                      style: AppTextStyles.regular12.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        height: 1.5,
                      ),
                    ),
                    value: entry.value,
                    onChanged: (value) => onChanged(entry.key, value),
                    secondary: state.isLoading && state.data == entry.key
                        ? SizedBox.square(
                            dimension: 20.r,
                            child: CustomLoading.showLoadingView(size: 20.r),
                          )
                        : null,
                  ),
                ).paddingOnly(bottom: 12),
            ],
          );
        },
      );
}
