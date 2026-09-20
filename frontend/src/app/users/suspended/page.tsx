'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { User, Eye, UserCheck } from 'lucide-react';
import { mockSuspendedUsers, suspendedUsersMetrics } from '@/data/mockData';

export default function SuspendedUsersPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'temp' | 'banned'>('all');

  const filteredUsers = mockSuspendedUsers.filter((user) => {
    if (activeTab === 'temp') return user.status === 'موقوف';
    if (activeTab === 'banned') return user.status === 'محظور';
    return true;
  });

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="المستخدمون الموقوفون والمحظورون"
        subtitle="إدارة الحسابات المعلقة، قرارات الحظر وإعادة التفعيل"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top 3 Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn">
            <div className="text-3xl font-black text-amber-500 dark:text-amber-400 mb-1">
              {suspendedUsersMetrics.tempSuspended}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              موقوف مؤقتاً
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn" style={{ animationDelay: '80ms' }}>
            <div className="text-3xl font-black text-rose-500 dark:text-rose-400 mb-1">
              {suspendedUsersMetrics.permanentlyBanned}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              محظور نهائياً
            </div>
          </div>

          <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn" style={{ animationDelay: '160ms' }}>
            <div className="text-3xl font-black text-blue-600 dark:text-blue-400 mb-1">
              {suspendedUsersMetrics.pendingDecision}
            </div>
            <div className="text-xs font-semibold text-[var(--text-subtle)]">
              بانتظار القرار
            </div>
          </div>
        </div>

        {/* Suspended Users Section */}
        <div className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6 animate-fadeInUp" style={{ animationDelay: '100ms' }}>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base">
              قائمة المستخدمين الموقوفين
            </h3>

            {/* Filter Pills */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'all'
                    ? 'bg-rose-600 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                الكل
              </button>
              <button
                onClick={() => setActiveTab('temp')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'temp'
                    ? 'bg-amber-500 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                موقوف مؤقتاً
              </button>
              <button
                onClick={() => setActiveTab('banned')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors ${
                  activeTab === 'banned'
                    ? 'bg-rose-600 text-white'
                    : 'bg-[var(--badge-bg-muted)] text-[var(--text-muted)] hover:bg-[var(--card-hover)]'
                }`}
              >
                محظور
              </button>
            </div>
          </div>

          {/* User List Rows */}
          <div className="divide-y divide-[var(--divider)]">
            {filteredUsers.map((user) => (
              <div
                key={user.id}
                className="py-4 flex flex-col sm:flex-row items-center justify-between gap-4 hover:bg-[var(--table-row-hover)] transition-colors px-2 rounded-xl"
              >
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  <div className="w-10 h-10 rounded-full bg-rose-50 dark:bg-rose-500/10 text-rose-500 dark:text-rose-400 flex items-center justify-center shrink-0 border border-rose-100 dark:border-rose-500/20">
                    <User className="w-5 h-5" />
                  </div>

                  <div>
                    <h4 className="font-bold text-[var(--foreground)] text-sm">
                      {user.name}
                    </h4>
                    <p className="text-xs text-[var(--text-subtle)] mt-0.5">
                      {user.suspensionReason} • {user.suspendedDate} • بواسطة{' '}
                      {user.suspendedBy}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  {user.status === 'موقوف' ? (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/20">
                      موقوف
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/20">
                      محظور
                    </span>
                  )}

                  <button className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors">
                    <UserCheck className="w-3.5 h-3.5" />
                    <span>رفع الإيقاف</span>
                  </button>

                  <Link
                    href={`/users/${user.id}`}
                    className="inline-flex items-center gap-1 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] text-[var(--foreground)] text-xs font-bold px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                    <span>عرض</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
