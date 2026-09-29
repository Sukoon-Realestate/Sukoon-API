import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/status_builder.dart';

import '../../data/enums/notification_role.dart';
import '../../data/models/notification_setting_content.dart';
import '../cubits/notification_settings_cubit.dart';
import '../widgets/notification_settings_content.dart';
import '../widgets/device_notification_permission_tile.dart';

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key, required this.role});

  final NotificationRole role;

  @override
  State<NotificationSettingsScreen> createState() =>
      _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState
    extends State<NotificationSettingsScreen> {
  late final NotificationSettingsCubit _settingsCubit;
  late final NotificationSettingUpdateCubit _updateCubit;
  late final Future<void> _settingsRequest;

  @override
  void initState() {
    super.initState();
    _settingsCubit = NotificationSettingsCubit();
    _updateCubit = NotificationSettingUpdateCubit();
    _settingsRequest = _settingsCubit.loadSettings();
  }

  @override
  void dispose() {
    unawaited(_settingsCubit.close());
    unawaited(_updateCubit.close());
    super.dispose();
  }

  Future<void> _updateSetting(
    NotificationSettingContent setting,
    bool value,
  ) async {
    if (_updateCubit.isLoading || !setting.canChange) return;

    _settingsCubit.updateSetting(setting.id, value);
    final bool succeeded = await _updateCubit.updateSetting(
      key: setting.id,
      value: value,
    );
    if (!succeeded) {
      _settingsCubit.updateSetting(setting.id, setting.isEnabled);
    }
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<NotificationSettingsCubit>.value(value: _settingsCubit),
        BlocProvider<NotificationSettingUpdateCubit>.value(value: _updateCubit),
      ],
      child: AppScaffold(
        title: LocaleKeys.notificationSettingsTitle,
        showBackButton: true,
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const DeviceNotificationPermissionTile(),
              Expanded(
                child:
                    BlocBuilder<
                      NotificationSettingUpdateCubit,
                      AsyncState<String>
                    >(
                      builder: (context, updateState) {
                        return StatusBuilder<
                          NotificationSettingsCubit,
                          NotificationSettingsContent
                        >.withShimmer(
                          initialDataForShimmer:
                              const NotificationSettingsContent.initial(),
                          requestToTryAgainWhenError: _settingsRequest,
                          onRetry: _settingsCubit.loadSettings,
                          errorType: ErrorType.defaultView,
                          builder: (settings) =>
                              NotificationSettingsContentView(
                                settings: settings,
                                updatingKey: updateState.isLoading
                                    ? updateState.data
                                    : null,
                                onSettingChanged: _updateSetting,
                              ),
                        );
                      },
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
