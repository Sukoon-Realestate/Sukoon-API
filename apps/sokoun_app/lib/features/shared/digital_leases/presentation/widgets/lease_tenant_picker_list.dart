import 'package:flutter/material.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_empty_state.dart';
import '../../data/models/lease_tenant.dart';
import '../../data/lease_tenants_data.dart';

class LeaseTenantPickerList extends StatefulWidget {
  const LeaseTenantPickerList({super.key, required this.propertyId});
  final String propertyId;
  @override
  State<LeaseTenantPickerList> createState() => _LeaseTenantPickerListState();
}

class _LeaseTenantPickerListState extends State<LeaseTenantPickerList> {
  final PagifyController<LeaseTenant> _controller = PagifyController();
  @override
  Widget build(BuildContext context) => AppPagify<LeaseTenant>(
    pagifyController: _controller,
    cacheKey: LeaseTenantsData.cacheKey(widget.propertyId),
    cacheToJson: (item) => item.toJson(),
    cacheFromJson: LeaseTenant.fromJson,
    asyncCall: (_, page) =>
        LeaseTenantsData.getPage(propertyId: widget.propertyId, page: page),
    emptyListView: const LeaseTenantsEmptyState(),
    itemBuilder: (_, __, ___, tenant) => ListTile(
      key: ValueKey(tenant.id),
      title: AppText(tenant.displayName),
      onTap: tenant.id.isEmpty ? null : () => Go.back(tenant),
    ),
  );
}

class LeaseTenantsEmptyState extends StatelessWidget {
  const LeaseTenantsEmptyState({super.key});
  @override
  Widget build(BuildContext context) => PremiumEmptyState(
    title: LocaleKeys.paidLeaseTenantEmpty,
    description: LocaleKeys.paidLeaseTenantEmptyBody,
  );
}
