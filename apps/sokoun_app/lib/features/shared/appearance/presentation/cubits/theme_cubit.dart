import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../data/theme_preferences.dart';

class ThemeCubit extends Cubit<ThemeMode> {
  ThemeCubit({required ThemeMode initialMode}) : super(initialMode);

  Future<void> setMode(ThemeMode mode) async {
    if (isClosed || mode == state) return;
    emit(mode);
    await ThemePreferences.write(mode);
  }
}
