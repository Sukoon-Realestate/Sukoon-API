import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/shared/models/user_enum.dart';

class SelectRoleCubit extends Cubit<UserType>{
  SelectRoleCubit() : super(UserType.unknown);

  void selectRole(UserType role){
    emit(role);
  }

  UserType get currentRole => state;
}