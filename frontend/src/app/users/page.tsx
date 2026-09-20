'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Search, Filter, Eye, UserX } from 'lucide-react';
import { mockUsers, userDistributionData } from '@/data/mockData';

export default function UserManagementPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'verified' | 'pending' | 'suspended'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredUsers = mockUsers.filter((user) => {
    // Search filter
    const matchesSearch =
      user.name.includes(searchQuery) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    // Tab filter
    if (activeTab === 'verified') return user.kycStatus === 'موثق';
    if (activeTab === 'pending') return user.kycStatus === 'قيد المراجعة';
    if (activeTab === 'suspended') return user.status === 'موقوف';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة المستخدمين"
        subtitle="قائمة المستخدمين المسجلين، حالة التوثيق والإجراءات الإدارية"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
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

            <button className="flex items-center gap-2 bg-[var(--card-bg)] px-4 py-2.5 rounded-xl border border-[var(--card-border)] text-sm font-semibold text-[var(--primary-text)] hover:bg-[var(--card-hover)] transition-colors shadow-[var(--shadow-card)]">
              <Filter className="w-4 h-4" />
              <span>فلتر</span>
            </button>
          </div>
        </div>

        {/* Tab Cards (Interactive Metric Filters) */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: الكل */}
          <button
            onClick={() => setActiveTab('all')}
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn ${
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
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn ${
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
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn ${
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
            className={`p-5 rounded-2xl border text-center transition-all animate-scaleIn ${
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
                {filteredUsers.length > 0 ? (
                  filteredUsers.map((user) => (
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
                            className="inline-flex items-center gap-1 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>عرض</span>
                          </Link>
                          <button className="inline-flex items-center gap-1 bg-rose-100 hover:bg-rose-200 text-rose-700 dark:bg-rose-500/15 dark:hover:bg-rose-500/25 dark:text-rose-400 text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                            <UserX className="w-3.5 h-3.5" />
                            <span>إيقاف</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={7}
                      className="py-12 text-center text-[var(--text-subtle)] font-medium"
                    >
                      لا يوجد مستخدمون يطابقون خيارات البحث أو التصفية الحالية.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
