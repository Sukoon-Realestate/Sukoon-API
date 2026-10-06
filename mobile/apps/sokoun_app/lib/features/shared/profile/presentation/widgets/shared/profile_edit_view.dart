part of '../../../imports.dart';

class ProfileEditView extends StatefulWidget {
  const ProfileEditView({
    super.key,
    required this.initialValue,
    required this.workspace,
  });

  final UserModel initialValue;
  final AppWorkspace workspace;

  @override
  State<ProfileEditView> createState() => _ProfileEditViewState();
}

class _ProfileEditViewState extends State<ProfileEditView> {
  final GlobalKey _nameFieldKey = GlobalKey();
  final GlobalKey _phoneFieldKey = GlobalKey();
  final GlobalKey<FormFieldState<ProfileGender>> _genderFieldKey =
      GlobalKey<FormFieldState<ProfileGender>>();
  late final TextEditingController _nameController;
  late final TextEditingController _phoneController;
  late final TextEditingController _emailController;
  late final ProfileEditCubit _editCubit;
  late final UserProfileCubit _profileCubit;
  late Future<void> _profileRequest;
  late UserModel _initialUser;
  ProfileGender _initialGender = ProfileGender.unspecified;
  String _birthDate = '';
  ProfileCity? _initialCity;
  final ValueNotifier<ProfileCity?> _city = ValueNotifier(null);
  final ValueNotifier<File?> _avatar = ValueNotifier<File?>(null);
  final ValueNotifier<ProfileGender> _gender = ValueNotifier<ProfileGender>(
    ProfileGender.unspecified,
  );

  Color get _accentColor => widget.workspace.isOwner
      ? AppColors.sokoonGold
      : context.appColor(AppColors.sokoonTeal);

  String get _title => widget.workspace.isOwner
      ? LocaleKeys.profileOwnerEditTitle
      : LocaleKeys.profileTenantEditTitle;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.initialValue.name);
    _phoneController = TextEditingController(text: widget.initialValue.phone);
    _emailController = TextEditingController(text: widget.initialValue.email);
    _initialUser = widget.initialValue;
    _editCubit = ProfileEditCubit();
    _profileCubit = UserProfileCubit();
    _profileRequest = _profileCubit.load(onLoaded: _applyProfile);
  }

  Future<void> _loadProfile() {
    if (_profileCubit.isLoading) return _profileRequest;
    return _profileRequest = _profileCubit.load(onLoaded: _applyProfile);
  }

  void _applyProfile(UserProfileContent profile) {
    if (!mounted) return;
    final bool nameChanged = _nameController.text.trim() != _initialUser.name;
    final bool phoneChanged =
        _phoneController.text.trim() != _initialUser.phone;
    final bool cityChanged = _city.value?.id != _initialCity?.id;
    final bool genderChanged = _gender.value != _initialGender;
    _initialUser = profile.toUser(_initialUser);
    if (!nameChanged) _nameController.text = _initialUser.name;
    if (!phoneChanged) _phoneController.text = _initialUser.phone;
    _emailController.text = _initialUser.email;
    _initialCity = profile.city;
    if (!cityChanged) _city.value = profile.city;
    _initialGender = ProfileGender.values.firstWhere(
      (gender) => gender.apiValue == profile.gender,
      orElse: () => ProfileGender.unspecified,
    );
    if (!genderChanged) {
      _gender.value = _initialGender;
      _genderFieldKey.currentState?.didChange(_initialGender);
    }
    _birthDate = profile.birthDate;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _avatar.dispose();
    _city.dispose();
    _gender.dispose();
    _editCubit.close();
    _profileCubit.close();
    super.dispose();
  }

  String _genderLabel(ProfileGender gender) {
    if (gender.isMale) return LocaleKeys.profileMale;
    if (gender.isFemale) return LocaleKeys.profileFemale;
    return LocaleKeys.notSetYet;
  }

  Future<void> _pickAvatar() async {
    final File? avatar = await Helpers.getImageFromCameraOrDevice();
    if (avatar != null && mounted) {
      final String? error = await Validators.validateAccountImage(
        avatar,
        allowGif: true,
      );
      if (!mounted) return;
      if (error != null) {
        Messages.showToast(msg: error, status: BaseStatus.error);
        return;
      }
      _avatar.value = avatar;
    }
  }

  Future<void> _pickGender() async {
    final ProfileGender? gender = await showModalBottomSheet<ProfileGender>(
      context: context,
      useSafeArea: true,
      backgroundColor: context.appColor(AppColors.white, surface: true),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
      ),
      builder: (_) => const _ProfileGenderSheet(),
    );
    if (gender != null && mounted) {
      _genderFieldKey.currentState?.didChange(gender);
      _gender.value = gender;
    }
  }

  Widget _buildGenderField({required bool isSaving}) {
    return FormField<ProfileGender>(
      key: _genderFieldKey,
      initialValue: _gender.value,
      validator: (gender) => Validators.validateGender(gender?.apiValue),
      builder: (field) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: 6.h,
          children: [
            ValueListenableBuilder<ProfileGender>(
              valueListenable: _gender,
              builder: (context, gender, _) => _ProfileReadonlyField(
                label: LocaleKeys.gender,
                value: _genderLabel(gender),
                onTap: isSaving ? null : _pickGender,
              ),
            ),
            if (field.hasError)
              AppText(
                field.errorText ?? '',
                style: AppTextStyles.regular11.copyWith(
                  color: context.appColor(AppColors.sokoonRose),
                  fontSize: 11.sp,
                  height: 1.45,
                ),
              ),
          ],
        );
      },
    );
  }

  Future<void> _save() async {
    if (_editCubit.isLoading || _profileCubit.isLoading) {
      return;
    }

    final ProfileEditBody body = ProfileEditBody(
      avatar: _avatar.value,
      fullName: _nameController.text.trim(),
      gender: _gender.value.apiValue,
      phoneNumber: _phoneController.text.trim(),
      cityId: _city.value?.id,
      updateCity: _city.value?.id != _initialCity?.id,
      updateGender: _gender.value != _initialGender,
    );
    final String? imageError = await Validators.validateAccountImage(
      body.avatar,
      allowGif: true,
    );
    if (!mounted || _editCubit.isLoading) return;
    if (imageError != null) {
      Messages.showToast(msg: imageError, status: BaseStatus.error);
      return;
    }

    bool wasUpdated = false;
    await _editCubit.editProfile(
      body: body,
      onSuccess: () => wasUpdated = true,
    );
    if (!wasUpdated || !mounted) return;

    final UserModel updatedUser = _initialUser.copyWith(
      name: body.fullName,
      phone: Validators.normalizeEgyptianMobile(body.phoneNumber),
    );
    await UserCubit.instance.updateUser(updatedUser);

    if (!mounted) {
      return;
    }
    Go.back(updatedUser);
  }

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _nameFieldKey,
      title: LocaleKeys.fullName,
      value: _nameController.text,
      validator: Validators.validateFullName,
    ),
    FirstValidationErrorField(
      fieldKey: _phoneFieldKey,
      title: LocaleKeys.phoneNumber,
      value: _phoneController.text,
      validator: Validators.validateEgyptianMobile,
    ),
    FirstValidationErrorField(
      fieldKey: _genderFieldKey,
      title: LocaleKeys.gender,
      value: _gender.value.apiValue,
      validator: Validators.validateGender,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider<ProfileEditCubit>.value(
      value: _editCubit,
      child: UnsavedChangesGuard(
        hasChanges: () =>
            _nameController.text.trim() != _initialUser.name ||
            _phoneController.text.trim() != _initialUser.phone ||
            _avatar.value != null ||
            _city.value?.id != _initialCity?.id ||
            _gender.value != _initialGender,
        isSaving: () => _editCubit.isLoading,
        child: BlocProvider<UserProfileCubit>.value(
          value: _profileCubit,
          child: FirstValidationErrorForm(
            validationFields: _validationFields,
            onValid: _save,
            builder: (context, submit) => _buildScaffold(submit),
          ),
        ),
      ),
    );
  }

  Widget _buildScaffold(VoidCallback submit) {
    return AppScaffold(
      title: _title,
      showBackButton: true,
      contentWidth: SokounContentWidth.form,
      actions: [
        BlocSelector<UserProfileCubit, AsyncState<UserProfileContent>, bool>(
          selector: (state) => state.isLoading,
          builder: (context, isLoading) =>
              BlocSelector<
                ProfileEditCubit,
                AsyncState<Map<String, dynamic>>,
                bool
              >(
                selector: (state) => state.isLoading,
                builder: (context, isSaving) => TextButton(
                  onPressed: isSaving || isLoading ? null : submit,
                  child: isSaving
                      ? SizedBox.square(
                          dimension: 18.r,
                          child: CustomLoading.showLoadingView(
                            color: context.appColor(AppColors.sokoonTeal),
                            size: 18.r,
                          ),
                        )
                      : AppText(
                          LocaleKeys.profileSave,
                          style: AppTextStyles.bold14.copyWith(
                            color: isLoading
                                ? context.appColor(AppColors.sokoonMuted)
                                : context.appColor(AppColors.sokoonTeal),
                            fontSize: 14.sp,
                            height: 1.45,
                          ),
                        ),
                ),
              ),
        ),
      ],
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: SafeArea(
        child:
            BlocSelector<
              ProfileEditCubit,
              AsyncState<Map<String, dynamic>>,
              bool
            >(
              selector: (state) => state.isLoading,
              builder: (context, isSaving) => ExcludeFocus(
                excluding: isSaving,
                child: AbsorbPointer(
                  absorbing: isSaving,
                  child: SingleChildScrollView(
                    padding: EdgeInsets.fromLTRB(20.w, 24.h, 20.w, 28.h),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        ValueListenableBuilder<File?>(
                          valueListenable: _avatar,
                          builder: (context, avatar, _) => Column(
                            spacing: 8.h,
                            children: [
                              BlocSelector<
                                UserProfileCubit,
                                AsyncState<UserProfileContent>,
                                String
                              >(
                                selector: (state) => state.data.avatar,
                                builder: (context, avatarUrl) =>
                                    ValueListenableBuilder<TextEditingValue>(
                                      valueListenable: _nameController,
                                      builder: (context, name, _) =>
                                          ProfileAvatar(
                                            name: name.text,
                                            avatarUrl: avatarUrl,
                                            imageFile: avatar,
                                            accentColor: _accentColor,
                                            backgroundColor: context.appColor(
                                              _accentColor,
                                              surface: true,
                                            ),
                                            size: 88,
                                            useInitial: true,
                                            badgeIcon:
                                                Icons.camera_alt_outlined,
                                            onBadgePressed: isSaving
                                                ? null
                                                : _pickAvatar,
                                          ),
                                    ),
                              ),
                              AppText(
                                LocaleKeys.profileChangePhoto,
                                style: AppTextStyles.bold13.copyWith(
                                  color: context.appColor(_accentColor),
                                  fontSize: 13.sp,
                                  height: 1.45,
                                ),
                              ),
                            ],
                          ),
                        ),
                        24.szH,
                        SokoonNameField(
                          key: _nameFieldKey,
                          controller: _nameController,
                          label: LocaleKeys.fullName,
                          hintText: LocaleKeys.fullNameHint,
                          accentColor: _accentColor,
                          validator: Validators.validateFullName,
                        ),
                        14.szH,
                        SokoonPhoneField(
                          key: _phoneFieldKey,
                          controller: _phoneController,
                          accentColor: _accentColor,
                          validator: Validators.validateEgyptianMobile,
                        ),
                        14.szH,
                        SokoonEmailField(
                          controller: _emailController,
                          accentColor: _accentColor,
                          action: TextInputAction.done,
                          readOnly: true,
                          validator: Validators.skipValidation,
                        ),
                        14.szH,
                        BlocBuilder<
                          UserProfileCubit,
                          AsyncState<UserProfileContent>
                        >(
                          builder: (context, state) {
                            if (state.isError) {
                              return ProfileEditLoadNotice.error(
                                message: state.msg,
                                onRetry: _loadProfile,
                              );
                            }
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              spacing: 10.h,
                              children: [
                                if (state.isLoading || state.isInitial)
                                  AppText(
                                    LocaleKeys.profileEditLoadingDetails,
                                    style: AppTextStyles.regular13.copyWith(
                                      color: context.appColor(
                                        AppColors.sokoonGray,
                                      ),
                                      fontSize: 13.sp,
                                      height: 1.45,
                                    ),
                                  ),
                                StatusBuilder<
                                  UserProfileCubit,
                                  UserProfileContent
                                >.withShimmer(
                                  initialDataForShimmer:
                                      const UserProfileContent.initial(),
                                  onRetry: _loadProfile,
                                  shimmerBuilder: (_) =>
                                      const ProfileEditLoadNotice.loading(),
                                  builder: (_) =>
                                      _buildAccountDetails(isSaving: isSaving),
                                ),
                              ],
                            );
                          },
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
      ),
    );
  }

  Widget _buildAccountDetails({required bool isSaving}) => Column(
    spacing: 14.h,
    children: [
      ValueListenableBuilder<ProfileCity?>(
        valueListenable: _city,
        builder: (context, city, _) => ProfileCitySelector(
          city: city,
          isSaving: isSaving,
          onChanged: (value) => _city.value = value,
        ),
      ),
      if (widget.workspace.isTenant)
        _ProfileReadonlyField(
          label: LocaleKeys.profileBirthDate,
          value: _birthDate.isEmpty ? LocaleKeys.notSetYet : _birthDate,
        ),
      _buildGenderField(isSaving: isSaving),
    ],
  );
}

class _ProfileReadonlyField extends StatelessWidget {
  const _ProfileReadonlyField({
    required this.label,
    required this.value,
    this.onTap,
  });

  final String label;
  final String value;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: 7.h,
      children: [
        AppText(
          label,
          style: AppTextStyles.bold13.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 13.sp,
            height: 1.45,
          ),
        ),
        Material(
          color: context.appColor(AppColors.white, surface: true),
          borderRadius: BorderRadius.circular(12.r),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(12.r),
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12.r),
                border: Border.all(
                  color: context.appColor(AppColors.sokoonBorder),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: AppText(
                      value,
                      style: AppTextStyles.semiBold.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                        fontSize: 14.sp,
                      ),
                    ),
                  ),
                  Icon(
                    Icons.arrow_forward_ios_rounded,
                    color: context.appColor(AppColors.sokoonGray),
                    size: 15.r,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ProfileGenderSheet extends StatelessWidget {
  const _ProfileGenderSheet();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(20.w, 18.h, 20.w, 24.h),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppText(
            LocaleKeys.gender,
            style: AppTextStyles.bold16.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 16.sp,
              height: 1.45,
            ),
          ),
          10.szH,
          _ProfileGenderOption(
            label: LocaleKeys.profileMale,
            onTap: () => Go.back(ProfileGender.male),
          ),
          Divider(height: 1, color: context.appColor(AppColors.sokoonBorder)),
          _ProfileGenderOption(
            label: LocaleKeys.profileFemale,
            onTap: () => Go.back(ProfileGender.female),
          ),
        ],
      ),
    );
  }
}

class _ProfileGenderOption extends StatelessWidget {
  const _ProfileGenderOption({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      title: AppText(
        label,
        style: AppTextStyles.bold14.copyWith(
          color: context.appColor(AppColors.sokoonNavy),
          fontSize: 14.sp,
          height: 1.45,
        ),
      ),
      trailing: Icon(
        Icons.chevron_right_rounded,
        color: context.appColor(AppColors.sokoonGray),
        size: 20.r,
      ),
      onTap: onTap,
    );
  }
}
