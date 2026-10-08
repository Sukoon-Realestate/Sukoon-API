import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

import '../../data/account_access.dart';
import 'verification_required_content.dart';

/// Does not mount the protected child until the current account is verified.
class VerifiedAccountGate extends StatelessWidget {
  const VerifiedAccountGate({
    super.key,
    required this.child,
    this.showBackButton = true,
  });

  final Widget child;
  final bool showBackButton;

  @override
  Widget build(BuildContext context) {
    if (!injector.isRegistered<UserCubit>()) return _content();
    return BlocBuilder<UserCubit, UserState>(
      bloc: UserCubit.instance,
      builder: (context, _) => _content(),
    );
  }

  Widget _content() => AccountAccess.isVerified
      ? child
      : AppScaffold(
          title: LocaleKeys.profileIdentityVerification,
          showBackButton: showBackButton,
          body: const SafeArea(child: VerificationRequiredContent()),
        );
}
