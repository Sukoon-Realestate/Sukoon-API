'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { EmptyState } from '@/components/ui/EmptyState';
import { Pagination } from '@/components/ui/Pagination';
import { Search, Filter, Eye, UserX, CheckCircle2 } from 'lucide-react';
import { mockUsers, userDistributionData, UserItem } from '@/data/mockData';

export default function UserManagementPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'verified' | 'pending' | 'suspended'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [usersList, setUsersList] = useState<UserItem[]>(mockUsers);
  const [selectedUserToSuspend, setSelectedUserToSuspend] = useState<UserItem | null>(null);
  const [showFilterDrawer, setShowFilterDrawer] = useState(false);
  const [roleFilter, setRoleFilter] = useState<'all' | 'مستأجر' | 'مالك'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const { showToast } = useToast();

  const filteredUsers = usersList.filter((user) => {
    // Search filter
    const matchesSearch =
      user.name.includes(searchQuery) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    // Role filter
    if (roleFilter !== 'all' && user.type !== roleFilter) return false;

    // Tab filter
    if (activeTab === 'verified') return user.kycStatus === 'موثق';
    if (activeTab === 'pending') return user.kycStatus === 'قيد المراجعة';
    if (activeTab === 'suspended') return user.status === 'موقوف';
    return true;
  });

  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleToggleSuspend = () => {
    if (!selectedUserToSuspend) return;
    const isCurrentlySuspended = selectedUserToSuspend.status === 'موقوف';

    setUsersList((prev) =>
      prev.map((u) =>
        u.id === selectedUserToSuspend.id
          ? { ...u, status: isCurrentlySuspended ? 'نشط' : 'موقوف' }
          : u
      )
    );

    showToast(
      isCurrentlySuspended
        ? `تم إلغاء إيقاف حساب ${selectedUserToSuspend.name} بنجاح`
        : `تم إيقاف حساب ${selectedUserToSuspend.name} بنجاح`,
      isCurrentlySuspended ? 'success' : 'error'
    );
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
        subtitle="قائمة المستخدمين المسجلين، حالة التوثيق والإجراءات الإدارية"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <Breadcrumbs />
        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 animate-fadeInUp">
          <div className="w-full sm:w-auto text-lg font-extrabold text-[var(--foreground)]">
            إدارة المستخدمين
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <div className="relative flex-1 sm:w-80">
              <input
                type="text"
                placeholder="بحث باسم أو بريد..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-4 pr-10 py-2.5 bg-[var(--input-bg)] rounded-xl border border-[var(--input-border)] text-sm text-[var(--foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--input-focus-ring)] focus:border-[var(--primary)] transition-all placeholder:text-[var(--text-subtle)]"
              />
              <Search className="w-4 h-4 text-[var(--text-subtle)] absolute right-3.5 top-3.5" />
            </div>

            <div className="relative">
              <button
                onClick={() => setShowFilterDrawer(!showFilterDrawer)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-semibold transition-colors shadow-[var(--shadow-card)] cursor-pointer ${
                  showFilterDrawer || roleFilter !== 'all'
                    ? 'bg-teal-700 text-white border-teal-800'
                    : 'bg-[var(--card-bg)] text-[var(--primary-text)] border-[var(--card-border)] hover:bg-[var(--card-hover)]'
                }`}
              >
                <Filter className="w-4 h-4" />
                <span>تصفية ({roleFilter === 'all' ? 'الكل' : roleFilter})</span>
              </button>

              {/* Filter Dropdown Drawer */}
              {showFilterDrawer && (
                <div className="absolute top-12 left-0 w-52 bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-xl p-3 z-30 animate-fadeInUp">
                  <p className="text-xs font-bold text-[var(--text-muted)] mb-2 px-1">تصفية حسب نوع الحساب:</p>
                  <div className="space-y-1">
                    <button
                      onClick={() => { setRoleFilter('all'); setShowFilterDrawer(false); }}
                      className={`w-full text-right px-3 py-2 rounded-xl text-xs font-bold transition-colors ${roleFilter === 'all' ? 'bg-teal-500/15 text-teal-600' : 'text-[var(--foreground)] hover:bg-[var(--card-hover)]'}`}
                    >
                      الكل (مستأجرين وملاك)
                    </button>
                    <button
                      onClick={() => { setRoleFilter('مستأجر'); setShowFilterDrawer(false); }}
                      className={`w-full text-right px-3 py-2 rounded-xl text-xs font-bold transition-colors ${roleFilter === 'مستأجر' ? 'bg-teal-500/15 text-teal-600' : 'text-[var(--foreground)] hover:bg-[var(--card-hover)]'}`}
                    >
                      مستأجرون فقط
                    </button>
                    <button
                      onClick={() => { setRoleFilter('مالك'); setShowFilterDrawer(false); }}
                      className={`w-full text-right px-3 py-2 rounded-xl text-xs font-bold transition-colors ${roleFilter === 'مالك' ? 'bg-teal-500/15 text-teal-600' : 'text-[var(--foreground)] hover:bg-[var(--card-hover)]'}`}
                    >
                      ملاك فقط
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tab Cards (Interactive Metric Filters) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: الكل */}
          <button
            onClick={() => setActiveTab('all')}
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn cursor-pointer ${
              activeTab === 'all'
                ? 'bg-teal-700 text-white border-teal-800 shadow-md scale-[1.02]'
                : 'bg-[var(--card-bg)] text-[var(--foreground)] border-[var(--card-border)] hover:border-[var(--text-subtle)] shadow-[var(--shadow-card)]'
            }`}
          >
            <div className="text-2xl font-black mb-1">
              {userDistributionData.total.toLocaleString()}
            </div>
            <div className={`text-xs font-semibold ${activeTab === 'all' ? 'text-teal-100' : 'text-[var(--text-muted)]'}`}>
              الكل
            </div>
          </button>

          {/* Card 2: موثق */}
          <button
            onClick={() => setActiveTab('verified')}
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn cursor-pointer ${
              activeTab === 'verified'
                ? 'bg-emerald-700 text-white border-emerald-800 shadow-md scale-[1.02]'
                : 'bg-[var(--card-bg)] text-[var(--foreground)] border-[var(--card-border)] hover:border-[var(--text-subtle)] shadow-[var(--shadow-card)]'
            }`}
            style={{ animationDelay: '50ms' }}
          >
            <div className={`text-2xl font-black mb-1 ${activeTab === 'verified' ? 'text-white' : 'text-emerald-600 dark:text-emerald-400'}`}>
              {userDistributionData.verified.toLocaleString()}
            </div>
            <div className={`text-xs font-semibold ${activeTab === 'verified' ? 'text-emerald-100' : 'text-[var(--text-muted)]'}`}>
              موثّق
            </div>
          </button>

          {/* Card 3: معلق */}
          <button
            onClick={() => setActiveTab('pending')}
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn cursor-pointer ${
              activeTab === 'pending'
                ? 'bg-amber-600 text-white border-amber-700 shadow-md scale-[1.02]'
                : 'bg-[var(--card-bg)] text-[var(--foreground)] border-[var(--card-border)] hover:border-[var(--text-subtle)] shadow-[var(--shadow-card)]'
            }`}
            style={{ animationDelay: '100ms' }}
          >
            <div className={`text-2xl font-black mb-1 ${activeTab === 'pending' ? 'text-white' : 'text-amber-500 dark:text-amber-400'}`}>
              {userDistributionData.pending}
            </div>
            <div className={`text-xs font-semibold ${activeTab === 'pending' ? 'text-amber-100' : 'text-[var(--text-muted)]'}`}>
              معلّق
            </div>
          </button>

          {/* Card 4: موقوف */}
          <button
            onClick={() => setActiveTab('suspended')}
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn cursor-pointer ${
              activeTab === 'suspended'
                ? 'bg-rose-600 text-white border-rose-700 shadow-md scale-[1.02]'
                : 'bg-[var(--card-bg)] text-[var(--foreground)] border-[var(--card-border)] hover:border-[var(--text-subtle)] shadow-[var(--shadow-card)]'
            }`}
            style={{ animationDelay: '150ms' }}
          >
            <div className={`text-2xl font-black mb-1 ${activeTab === 'suspended' ? 'text-white' : 'text-rose-500 dark:text-rose-400'}`}>
              {userDistributionData.suspended}
            </div>
            <div className={`text-xs font-semibold ${activeTab === 'suspended' ? 'text-rose-100' : 'text-[var(--text-muted)]'}`}>
              موقوف
            </div>
          </button>
        </div>

        {/* Users Table */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] overflow-hidden animate-fadeInUp" style={{ animationDelay: '200ms' }}>
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] border-b border-[var(--card-border)] text-[var(--text-muted)] text-xs font-bold">
                  <th className="py-4 px-6">الاسم</th>
                  <th className="py-4 px-6">النوع</th>
                  <th className="py-4 px-6">البريد</th>
                  <th className="py-4 px-6">الحالة</th>
                  <th className="py-4 px-6">التوثيق</th>
                  <th className="py-4 px-6">تاريخ التسجيل</th>
                  <th className="py-4 px-6 text-center">إجراء</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--table-border)] text-sm">
                {paginatedUsers.length > 0 ? (
                  paginatedUsers.map((user) => (
                    <tr
                      key={user.id}
                      className="hover:bg-[var(--table-row-hover)] transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-[var(--foreground)]">
                        {user.name}
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge type="userType" value={user.type} />
                      </td>
                      <td className="py-4 px-6 text-[var(--text-muted)] font-mono text-xs dir-ltr text-right">
                        {user.email}
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge type="userStatus" value={user.status} />
                      </td>
                      <td className="py-4 px-6">
                        <StatusBadge type="kycStatus" value={user.kycStatus} />
                      </td>
                      <td className="py-4 px-6 text-xs font-medium text-[var(--text-muted)]">
                        {user.regDate}
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center justify-center gap-2">
                          <Link
                            href={`/users/${user.id}`}
                            className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer btn-press"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>عرض</span>
                          </Link>
                          <button
                            onClick={() => setSelectedUserToSuspend(user)}
                            className={`inline-flex items-center gap-1 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer btn-press ${
                              user.status === 'موقوف'
                                ? 'bg-emerald-100 hover:bg-emerald-200 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'
                                : 'bg-rose-100 hover:bg-rose-200 text-rose-700 dark:bg-rose-500/15 dark:text-rose-400'
                            }`}
                          >
                            {user.status === 'موقوف' ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>تنشيط</span>
                              </>
                            ) : (
                              <>
                                <UserX className="w-3.5 h-3.5" />
                                <span>إيقاف</span>
                              </>
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="p-0 border-0">
                      <EmptyState
                        title="لم نجد أي مستخدم يطابق معايير البحث"
                        description="تأكد من كتابة الاسم أو البريد بشكل صحيح، أو أعد ضبط خيارات التصفية النشطة."
                        onReset={handleResetFilters}
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={Math.ceil(filteredUsers.length / itemsPerPage)}
            totalItems={filteredUsers.length}
            itemsPerPage={itemsPerPage}
            onPageChange={setCurrentPage}
            onItemsPerPageChange={(size) => {
              setItemsPerPage(size);
              setCurrentPage(1);
            }}
          />
        </div>
      </div>

      {/* Suspend Confirm Modal */}
      <ConfirmModal
        isOpen={!!selectedUserToSuspend}
        onClose={() => setSelectedUserToSuspend(null)}
        onConfirm={handleToggleSuspend}
        title={
          selectedUserToSuspend?.status === 'موقوف'
            ? `إلغاء إيقاف حساب ${selectedUserToSuspend?.name}`
            : `تأكيد إيقاف حساب ${selectedUserToSuspend?.name}`
        }
        message={
          selectedUserToSuspend?.status === 'موقوف'
            ? 'هل أنت تأكد من رغبتك في إعادة تفعيل حساب المستخدم وتمكينه من استخدام المنصة؟'
            : 'هل أنت تأكد من رغبتك في إيقاف حساب المستخدم؟ لن يتمكن من تسجيل الدخول حتى إلغاء الإيقاف.'
        }
        variant={selectedUserToSuspend?.status === 'موقوف' ? 'success' : 'danger'}
        confirmText={selectedUserToSuspend?.status === 'موقوف' ? 'تنشيط الحساب' : 'إيقاف الحساب'}
      />
    </div>
  );
}

