part of 'user_cubit.dart';



enum UserStatus {
  loggedIn,
  loggedOut,
}

class UserState extends Equatable {
  final UserModel userModel;
  final UserStatus userStatus;

  const UserState(
      {required this.userModel,
      this.userStatus = UserStatus.loggedOut,
      });

  factory UserState.initial() {
    return UserState(
        userModel: UserModel.initial(),
        userStatus: UserStatus.loggedOut,
        );
  }

  UserState copyWith(
      {UserModel? userModel,
      UserStatus? userStatus,
   }) {
    return UserState(
        userModel: userModel ?? this.userModel,
        userStatus: userStatus ?? this.userStatus,
        );
  }

  @override
  List<Object?> get props => [userModel, userStatus];
}
