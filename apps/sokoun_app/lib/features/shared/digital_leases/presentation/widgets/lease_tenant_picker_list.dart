import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:flutter/material.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_empty_state.dart';
import '../../data/models/lease_tenant.dart';
import '../../data/lease_tenants_data.dart';
import '../../../tenancy_invitations/data/tenancy_invitation_capabilities.dart';

class LeaseTenantPickerList extends StatefulWidget {
  const LeaseTenantPickerList({
    super.key,
    required this.propertyId,
    this.offerId = '',
  });
  final String propertyId;
  final String offerId;
  @override
  State<LeaseTenantPickerList> createState() => _LeaseTenantPickerListState();
}

class _LeaseTenantPickerListState extends State<LeaseTenantPickerList> {
  final PagifyController<LeaseTenant> _controller = PagifyController();
  @override
  Widget build(BuildContext context) => AppPagify<LeaseTenant>(
    pagifyController: _controller,
    cacheKey: LeaseTenantsData.cacheKey(
      widget.propertyId,
      offerId: widget.offerId,
    ),
    cachePolicy: ReadCachePolicy.privateMemory,
    cacheToJson: (item) => item.toJson(),
    cacheFromJson: LeaseTenant.fromJson,
    asyncCall: (_, page) => LeaseTenantsData.getPage(
      propertyId: widget.propertyId,
      page: page,
      offerId: widget.offerId,
    ),
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
    description: TenancyInvitationCapabilities.current.enabled
        ? LocaleKeys.tenancyInviteFromRequests
        : LocaleKeys.paidLeaseTenantEmptyBody,
  );
}
