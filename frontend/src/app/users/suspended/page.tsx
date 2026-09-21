'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { useToast } from '@/components/ui/Toast';
import { User, Eye, UserCheck } from 'lucide-react';
import { fetchUsers, unsuspendUser } from '@/lib/api/users';
import { UserItem } from '@/lib/api/types';

export default function SuspendedUsersPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'temp' | 'banned'>('all');
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { showToast } = useToast();

  const loadSuspended = async () => {
    setIsLoading(true);
    try {
      const res = await fetchUsers({ status: 'suspended' });
      if (res && res.results) {
        setUsers(res.results);
      } else {
        setUsers([]);
      }
    } catch (err) {
      console.error('Could not fetch suspended users from API:', err);
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSuspended();
  }, []);

  const filteredUsers = users.filter((user) => {
    if (activeTab === 'temp') return user.status === 'موقوف';
    if (activeTab === 'banned') return user.status === 'محظور';
    return true;
  });

  const handleUnsuspend = async (targetUser: UserItem) => {
    try {
      await unsuspendUser(targetUser.id);
      setUsers((prev) => prev.filter((u) => u.id !== targetUser.id));
      showToast(`تم رفع الإيقاف عن حساب ${targetUser.name} بنجاح`, 'success');
    } catch {
      showToast(`حدث خطأ أثناء رفع الإيقاف عن ${targetUser.name}`, 'error');
    }
  };

  const tempCount = users.filter((u) => u.status === 'موقوف').length;
  const bannedCount = users.filter((u) => u.status === 'محظور').length;

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="المستخدمون الموقوفون والمحظورون"
        subtitle="إدارة الحسابات المعلقة، قرارات الحظر وإعادة التفعيل"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn">
            <div className="text-3xl font-black text-amber-400 mb-1">
              {tempCount}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              موقوف مؤقتاً
            </div>
          </div>

          <div
            className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn"
            style={{ animationDelay: '80ms' }}
          >
            <div className="text-3xl font-black text-rose-400 mb-1">
              {bannedCount}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              محظور نهائياً
            </div>
          </div>

          <div
            className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] text-center animate-scaleIn"
            style={{ animationDelay: '160ms' }}
          >
            <div className="text-3xl font-black text-blue-400 mb-1">
              {users.length}
            </div>
            <div className="text-xs font-semibold text-slate-400">
              إجمالي الحسابات المعلقة
            </div>
          </div>
        </div>

        {/* Suspended Users Section */}
        <div
          className="bg-[var(--card-bg)] rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] p-6 space-y-6 animate-fadeInUp"
          style={{ animationDelay: '100ms' }}
        >
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <h3 className="font-extrabold text-white text-base">
              قائمة المستخدمين الموقوفين
            </h3>

            {/* Filter Pills */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('all')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'all'
                    ? 'bg-rose-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                الكل ({users.length})
              </button>
              <button
                onClick={() => setActiveTab('temp')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'temp'
                    ? 'bg-amber-500 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                موقوف مؤقتاً ({tempCount})
              </button>
              <button
                onClick={() => setActiveTab('banned')}
                className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                  activeTab === 'banned'
                    ? 'bg-rose-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                محظور ({bannedCount})
              </button>
            </div>
          </div>

          {/* User List Rows */}
          <div className="divide-y divide-[var(--divider)]">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">
                جاري تحميل المستخدمين الموقوفين...
              </div>
            ) : filteredUsers.length > 0 ? (
              filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="py-4 flex flex-col sm:flex-row items-center justify-between gap-4 hover:bg-slate-800/40 transition-colors px-2 rounded-xl"
                >
                  <div className="flex items-center gap-4 w-full sm:w-auto">
                    <div className="w-10 h-10 rounded-full bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0 border border-rose-500/20">
                      <User className="w-5 h-5" />
                    </div>

                    <div>
                      <h4 className="font-bold text-white text-sm">
                        {user.name}
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {user.email} • تاريخ التسجيل: {user.regDate}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-300 border border-amber-500/20">
                      {user.status}
                    </span>

                    <button
                      onClick={() => handleUnsuspend(user)}
                      className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>رفع الإيقاف</span>
                    </button>

                    <Link
                      href={`/users/${user.id}`}
                      className="inline-flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5 text-slate-400" />
                      <span>عرض</span>
                    </Link>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-slate-400">
                لا يوجد مستخدمون موقوفون حالياً في النظام.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
