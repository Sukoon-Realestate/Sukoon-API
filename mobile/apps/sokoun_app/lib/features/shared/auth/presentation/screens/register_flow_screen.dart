import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import '../cubits/register.dart';
import 'login_screen.dart';
import 'otp_screen.dart';
import 'register_screen.dart';

class RegisterFlowScreen extends StatefulWidget {
  const RegisterFlowScreen({super.key});

  @override
  State<RegisterFlowScreen> createState() => _RegisterFlowScreenState();
}

class _RegisterFlowScreenState extends State<RegisterFlowScreen> {
  late final RegisterCubit _cubit;
  final ValueNotifier<String?> _registeredEmail = ValueNotifier(null);

  @override
  void initState() {
    super.initState();
    _cubit = RegisterCubit();
  }

  @override
  void dispose() {
    _cubit.close();
    _registeredEmail.dispose();
    super.dispose();
  }

  Future<void> _register() => _cubit.register(
    onSuccess: (body) {
      if (mounted) _registeredEmail.value = body.email;
    },
  );

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _cubit,
    child: ValueListenableBuilder<String?>(
      valueListenable: _registeredEmail,
      builder: (context, email, _) => email == null
          ? BlocBuilder<RegisterCubit, AsyncState<Map<String, dynamic>>>(
              builder: (context, state) => PopScope(
                canPop: !state.isLoading,
                child: AbsorbPointer(
                  absorbing: state.isLoading,
                  child: RegisterScreen(
                    onSubmit: _register,
                    isSubmitting: state.isLoading,
                  ),
                ),
              ),
            )
          : OtpScreen(
              email: email,
              onVerified: () => Go.offAll(const LoginScreen()),
            ),
    ),
  );
}
