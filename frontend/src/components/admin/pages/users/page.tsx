'use client';

import React, { useState, useEffect } from 'react';
import Link from '@/components/ui/AdminLink';
import { TableScroll } from '@/components/ui/TableScroll';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { Search, Filter, Eye, UserX, CheckCircle2 } from 'lucide-react';
import { fetchUsers, suspendUser, unsuspendUser } from '@/lib/api/users';
import { UserItem } from '@/lib/api/types';
import { LogoLoader } from '@/components/ui/LogoLoader';

export default function UserManagementPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'verified' | 'pending' | 'suspended'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [usersList, setUsersList] = useState<UserItem[]>([]);
  const [selectedUserToSuspend, setSelectedUserToSuspend] = useState<UserItem | null>(null);
  const [showFilterDrawer, setShowFilterDrawer] = useState(false);
  const [roleFilter, setRoleFilter] = useState<'all' | 'مستأجر' | 'مالك'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const [totalCount, setTotalCount] = useState(0);
  const [loadedKey, setLoadedKey] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [loadError, setLoadError] = useState('');
  const queryKey = JSON.stringify([currentPage, itemsPerPage, searchQuery, roleFilter, activeTab, refresh]);
  const isLoading = loadedKey !== queryKey;
  const { showToast } = useToast();

  useEffect(() => {
    const controller = new AbortController();
    const params: import('@/lib/api/users').FetchUsersParams = { page: currentPage, page_size: itemsPerPage };
    if (searchQuery.trim()) params.search = searchQuery.trim();
    if (roleFilter !== 'all') params.role = roleFilter;
    if (activeTab === 'verified') params.kyc_status = 'verified';
    if (activeTab === 'pending') params.kyc_status = 'pending';
    if (activeTab === 'suspended') params.status = 'suspended';
    void fetchUsers(params, controller.signal).then(response => {
      if (controller.signal.aborted) return;
      setUsersList(response.results); setTotalCount(response.count); setLoadError('');
    }).catch(() => {
      if (!controller.signal.aborted) { setUsersList([]); setTotalCount(0); setLoadError('تعذر تحميل قائمة المستخدمين. أعد المحاولة.'); }
    }).finally(() => { if (!controller.signal.aborted) setLoadedKey(queryKey); });
    return () => controller.abort();
  }, [queryKey, currentPage, itemsPerPage, searchQuery, roleFilter, activeTab]);

  const handleConfirmSuspend = async () => {
    if (!selectedUserToSuspend) return;
    try {
      const isSuspended = selectedUserToSuspend.status === 'موقوف';
      if (isSuspended) {
        await unsuspendUser(selectedUserToSuspend.id);
        showToast(`تم رفع الإيقاف عن حساب ${selectedUserToSuspend.name} بنجاح`, 'success');
      } else {
        await suspendUser(selectedUserToSuspend.id);
        showToast(`تم إيقاف حساب ${selectedUserToSuspend.name} بنجاح`, 'error');
      }
      setRefresh(value => value + 1);
    } catch {
      showToast('حدث خطأ أثناء تحديث حالة المستخدم', 'error');
    } finally {
      setSelectedUserToSuspend(null);
    }
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setRoleFilter('all');
    setActiveTab('all');
    setCurrentPage(1);
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة المستخدمين"
        subtitle="متابعة الحسابات، تفاصيل التوثيق، صلاحيات الوصول والإجراءات الإدارية"
      />

      <div className="admin-page-body min-w-0 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <Breadcrumbs items={[{ label: 'الرئيسية', href: '/' }, { label: 'المستخدمون' }]} />
        {loadError && !isLoading && <p role="alert">{loadError}<button className="min-h-12 underline px-3" onClick={() => setRefresh(value => value + 1)}>إعادة المحاولة</button></p>}

        {/* Search & Tabs Controls */}
        {/* Search & Tabs Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          {/* Tab Navigation */}
          <div className="flex items-center gap-1.5 p-1 bg-[var(--card-hover)] dark:bg-[var(--card-hover)] rounded-2xl border border-[var(--card-border)] dark:border-[var(--card-border)] self-start">
            {[
              { id: 'all', label: 'الكل' },
              { id: 'verified', label: 'موثقون' },
              { id: 'pending', label: 'قيد المراجعة' },
              { id: 'suspended', label: 'موقوفون' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as typeof activeTab);
                  setCurrentPage(1);
                }}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === tab.id
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-[var(--foreground)]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Input & Filter Toggle */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1 sm:w-64">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="بحث بالاسم أو البريد..."
                className="w-full pl-4 pr-10 py-2.5 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-xl text-xs text-[var(--foreground)] placeholder-[var(--text-subtle)] focus:outline-none focus:border-teal-500/50"
              />
              <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3 top-3" />
            </div>

            <button
              onClick={() => setShowFilterDrawer(!showFilterDrawer)}
              className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 text-xs font-bold ${
                showFilterDrawer || roleFilter !== 'all'
                  ? 'bg-teal-500/15 border-teal-500/30 text-teal-600 dark:text-teal-400'
                  : 'bg-[var(--card-bg)] border-[var(--card-border)] text-[var(--text-muted)] hover:text-[var(--foreground)]'
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>تصفية</span>
            </button>
          </div>
        </div>

        {/* Filter Drawer */}
        {showFilterDrawer && (
          <div className="p-4 bg-[var(--card-hover)] border border-[var(--card-border)] rounded-2xl flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <span className="text-xs text-[var(--text-muted)] font-bold">نوع المستخدم:</span>
              <div className="flex items-center gap-2">
                {['all', 'مستأجر', 'مالك'].map((r) => (
                  <button
                    key={r}
                    onClick={() => {
                      setRoleFilter(r as typeof roleFilter);
                      setCurrentPage(1);
                    }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                      roleFilter === r
                        ? 'bg-teal-600 text-white shadow-xs'
                        : 'bg-[var(--card-bg)] text-[var(--text-muted)] hover:text-[var(--foreground)] border border-[var(--card-border)]'
                    }`}
                  >
                    {r === 'all' ? 'جميع الأدوار' : r}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleResetFilters}
              className="text-xs text-[var(--text-muted)] hover:text-rose-500 font-bold transition-colors cursor-pointer"
            >
              إعادة تعيين
            </button>
          </div>
        )}

        {/* Users Table Card */}
        <div className="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-[var(--shadow-card)] overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center text-[var(--text-muted)] text-xs font-bold space-y-3">
              <LogoLoader showLabel label="جاري تحميل بيانات المستخدمين من الخادم..." />
            </div>
          ) : usersList.length === 0 ? (
            <EmptyState
              title="لا يوجد مستخدمون"
              description="لم يتم العثور على أي مستخدمين يطابقون معايير البحث الحالية."
              actionLabel="إعادة ضبط الفلاتر"
              onAction={handleResetFilters}
            />
          ) : (
            <TableScroll>
              <table className="w-full text-right text-xs">
                <thead className="bg-[var(--table-header-bg)] border-b border-[var(--card-border)] text-[var(--text-muted)] font-bold">
                  <tr>
                    <th className="py-3.5 px-4">المستخدم</th>
                    <th className="py-3.5 px-4">النوع</th>
                    <th className="py-3.5 px-4">حالة الحساب</th>
                    <th className="py-3.5 px-4">حالة التوثيق (KYC)</th>
                    <th className="py-3.5 px-4">تاريخ التسجيل</th>
                    <th className="py-3.5 px-4">رقم الهاتف</th>
                    <th className="py-3.5 px-4">الإجراءات</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--divider)] font-medium">
                  {usersList.map((user) => (
                    <tr
                      key={user.id}
                      className="hover:bg-[var(--table-row-hover)] transition-colors group"
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center font-black text-teal-600 dark:text-teal-400 text-xs shrink-0">
                            {user.name.charAt(0)}
                          </div>
                          <div>
                            <Link
                              href={`/users/${user.id}`}
                              className="font-bold text-[var(--foreground)] hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
                            >
                              {user.name}
                            </Link>
                            <div className="text-[11px] text-[var(--text-subtle)] font-mono">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <StatusBadge type="role" value={user.type} />
                      </td>

                      <td className="py-3.5 px-4">
                        <StatusBadge status={user.status} />
                      </td>

                      <td className="py-3.5 px-4">
                        <StatusBadge status={user.kycStatus} />
                      </td>

                      <td className="py-3.5 px-4 text-[var(--text-muted)] font-mono">
                        {user.regDate}
                      </td>

                      <td className="py-3.5 px-4 text-[var(--text-muted)] font-mono dir-ltr text-right">
                        {user.phone || '–'}
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-1.5">
                          <Link
                            href={`/users/${user.id}`}
                            className="p-1.5 text-[var(--text-muted)] hover:text-teal-600 hover:bg-[var(--card-hover)] rounded-lg transition-colors"
                            title="عرض التفاصيل"
                          >
                            <Eye className="w-4 h-4" />
                          </Link>
                          <button
                            onClick={() => setSelectedUserToSuspend(user)}
                            className={`p-1.5 rounded-lg transition-colors ${
                              user.status === 'موقوف'
                                ? 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10'
                                : 'text-[var(--text-muted)] hover:text-rose-600 hover:bg-[var(--card-hover)]'
                            }`}
                            title={user.status === 'موقوف' ? 'إلغاء الإيقاف' : 'إيقاف الحساب'}
                          >
                            {user.status === 'موقوف' ? (
                              <CheckCircle2 className="w-4 h-4" />
                            ) : (
                              <UserX className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
          )}

          {/* Pagination */}
          {!isLoading && totalCount > itemsPerPage && (
            <div className="p-4 border-t border-[var(--card-border)] bg-[var(--table-header-bg)]">
              <Pagination
                currentPage={currentPage}
                totalItems={totalCount}
                pageSize={itemsPerPage}
                onPageChange={(p) => setCurrentPage(p)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {selectedUserToSuspend && (
        <ConfirmModal
          isOpen={Boolean(selectedUserToSuspend)}
          title={
            selectedUserToSuspend.status === 'موقوف'
              ? 'تأكيد تفعيل الحساب'
              : 'تأكيد إيقاف الحساب'
          }
          description={`هل أنت متأكد من تغيير حالة حساب المستخدم "${selectedUserToSuspend.name}"؟`}
          confirmLabel={selectedUserToSuspend.status === 'موقوف' ? 'تفعيل' : 'إيقاف'}
          confirmVariant={selectedUserToSuspend.status === 'موقوف' ? 'primary' : 'danger'}
          onConfirm={handleConfirmSuspend}
          onCancel={() => setSelectedUserToSuspend(null)}
        />
      )}
    </div>
  );
}
