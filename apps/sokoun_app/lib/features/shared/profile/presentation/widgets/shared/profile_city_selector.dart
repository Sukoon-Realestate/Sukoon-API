part of '../../../imports.dart';

class ProfileCitySelector extends StatelessWidget {
  const ProfileCitySelector({
    super.key,
    required this.city,
    required this.onChanged,
    required this.isSaving,
  });

  final ProfileCity? city;
  final ValueChanged<ProfileCity?> onChanged;
  final bool isSaving;

  Future<void> _chooseCity(BuildContext context) async {
    final result = await showModalBottomSheet<({ProfileCity? city})>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => const ProfileCityPicker(),
    );
    if (result != null && context.mounted) onChanged(result.city);
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      AppText(
        LocaleKeys.city,
        style: AppTextStyles.bold13.copyWith(
          color: context.appColor(AppColors.sokoonNavy),
        ),
      ),
      7.szH,
      OutlinedButton(
        onPressed: isSaving ? null : () => _chooseCity(context),
        child: Row(
          children: [
            Expanded(child: AppText(city?.name ?? LocaleKeys.notSetYet)),
            const Icon(Icons.expand_more_rounded),
          ],
        ),
      ),
    ],
  );
}

class ProfileCityPicker extends StatefulWidget {
  const ProfileCityPicker({super.key});
  @override
  State<ProfileCityPicker> createState() => _ProfileCityPickerState();
}

class _ProfileCityPickerState extends State<ProfileCityPicker> {
  final PagifyController<ProfileCity> _controller = PagifyController();

  @override
  Widget build(BuildContext context) => SizedBox(
    height: MediaQuery.sizeOf(context).height * .7,
    child: Column(
      children: [
        Padding(
          padding: EdgeInsets.all(16.w),
          child: Row(
            children: [
              Expanded(
                child: AppText(LocaleKeys.city, style: AppTextStyles.bold16),
              ),
              TextButton(
                onPressed: () => Go.back((city: null)),
                child: AppText(LocaleKeys.profileClearCity),
              ),
            ],
          ),
        ),
        Expanded(
          child: AppPagify<ProfileCity>(
            pagifyController: _controller,
            shrinkWrap: false,
            asyncCall: (_, page) => ProfileCitiesData.getPage(page),
            cacheKey: ProfileCitiesData.cacheKey,
            cachePolicy: ReadCachePolicy.privateMemory,
            cacheToJson: (city) => city.toJson(),
            cacheFromJson: ProfileCity.fromJson,
            emptyListView: const ProfileCitiesEmptyState(),
            itemBuilder: (context, cities, index, city) => ListTile(
              title: AppText(city.name),
              onTap: () => Go.back((city: city)),
            ),
          ),
        ),
      ],
    ),
  );
}
