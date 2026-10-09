import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:flutter/material.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/properties/data/owner_properties_data.dart';
import 'package:sokoun_app/features/owner/properties/data/enums/owner_property_filter.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'premium_empty_state.dart';

class PremiumPropertyPickerList extends StatefulWidget {
  const PremiumPropertyPickerList({super.key});
  @override
  State<PremiumPropertyPickerList> createState() =>
      _PremiumPropertyPickerListState();
}

class _PremiumPropertyPickerListState extends State<PremiumPropertyPickerList> {
  final PagifyController<OwnerPropertyContent> _controller = PagifyController();
  @override
  Widget build(BuildContext context) => AppPagify<OwnerPropertyContent>(
    pagifyController: _controller,
    asyncCall: (_, page) => OwnerPropertiesData.getOwnedPropertiesPage(
      page: page,
      filter: OwnerPropertyFilter.accepted,
    ),
    cacheKey: OwnerPropertiesData.cacheKeyFor(OwnerPropertyFilter.accepted),
    cachePolicy: ReadCachePolicy.privateMemory,
    cacheToJson: (item) => item.toJson(),
    cacheFromJson: OwnerPropertyContent.fromJson,
    emptyListView: PremiumEmptyState(
      title: LocaleKeys.paidPropertyEmpty,
      description: LocaleKeys.paidPropertyEmptyBody,
    ),
    itemBuilder: (_, __, ___, property) => ListTile(
      key: ValueKey(property.id),
      title: AppText(property.title),
      subtitle: AppText(property.location),
      onTap: property.id.isEmpty ? null : () => Go.back(property),
    ),
  );
}
