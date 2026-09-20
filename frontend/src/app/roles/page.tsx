'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { ConfirmModal } from '@/components/ui/ConfirmModal';
import { useToast } from '@/components/ui/Toast';
import { Plus, User, Check, X, ShieldAlert } from 'lucide-react';
import {
  mockAdminRoles,
  mockAdminUsers,
  mockPermissionsMatrix as initialMatrix,
  AdminUserItem,
} from '@/data/mockData';

export default function AdminRolesPage() {
  const [adminsList, setAdminsList] = useState<AdminUserItem[]>(mockAdminUsers);
  const [matrix, setMatrix] = useState(initialMatrix);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newAdminName, setNewAdminName] = useState('');
  const [newAdminRole, setNewAdminRole] = useState('مراجع KYC');
  const [adminToDelete, setAdminToDelete] = useState<AdminUserItem | null>(null);
  const { showToast } = useToast();

  const handleInviteAdmin = () => {
    if (!newAdminName.trim()) {
      showToast('يرجى كتابة اسم المشرف الجديد', 'error');
      return;
    }
    const created: AdminUserItem = {
      id: `admin-${Date.now()}`,
      name: newAdminName,
      roleName: newAdminRole,
      timeAgo: 'الآن',
      avatarColor: 'bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-400',
    };
    setAdminsList((prev) => [...prev, created]);
    showToast(`تم إرسال دعوة الانضمام إلى ${newAdminName} بدور ${newAdminRole}`, 'success');
    setNewAdminName('');
    setShowInviteModal(false);
  };

  const handleDeleteAdmin = () => {
    if (!adminToDelete) return;
    setAdminsList((prev) => prev.filter((a) => a.id !== adminToDelete.id));
    showToast(`تم حذف المشرف ${adminToDelete.name} وسحب كافة الصلاحيات`, 'error');
  };

  const toggleMatrixCell = (rowIndex: number, colKey: 'systemOwner' | 'mainAdmin' | 'kycReviewer' | 'propertyReviewer' | 'support') => {
    setMatrix((prev) =>
      prev.map((row, idx) =>
        idx === rowIndex ? { ...row, [colKey]: !row[colKey] } : row
      )
    );
    showToast('تم تحديث مصفوفة الصلاحيات بنجاح', 'info');
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة أدوار المشرفين"
        subtitle="صلاحيات فريق العمل، الأدوار القيادية وتخصيص مستويات الوصول"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Section: Roles & Admins */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Roles & Permissions (6 cols) */}
          <div className="lg:col-span-6 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              الأدوار والصلاحيات
            </h3>

            <div className="space-y-3">
              {mockAdminRoles.map((role) => (
                <div
                  key={role.id}
                  className="p-3.5 rounded-xl border border-[var(--card-border)] bg-[var(--card-hover)]/50 hover:bg-[var(--card-hover)] transition-all flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${role.color}`}></span>
                      <h4 className="font-bold text-[var(--foreground)] text-sm">
                        {role.name}
                      </h4>
                    </div>
                    {role.subtext && (
                      <p className="text-xs text-[var(--text-subtle)] font-medium">
                        {role.subtext}
                      </p>
                    )}
                    {role.badges && role.badges.length > 0 && (
                      <div className="flex items-center gap-1.5 pt-1">
                        {role.badges.map((badge, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--badge-bg-muted)] text-[var(--text-muted)] border border-[var(--card-border)]"
                          >
                            {badge}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <div className="text-center px-2">
                      <span className="font-extrabold text-[var(--foreground)] text-sm block leading-none">
                        {role.userCount}
                      </span>
                      <span className="text-[10px] text-[var(--text-subtle)] font-medium">
                        مستخدم
                      </span>
                    </div>

                    <button
                      onClick={() => showToast(`تعديل إعدادات دور ${role.name}`, 'info')}
                      className="px-3 py-1 bg-[var(--badge-bg-muted)] hover:bg-[var(--card-hover)] text-[var(--foreground)] font-bold rounded-lg border border-[var(--card-border)] transition-colors text-xs cursor-pointer"
                    >
                      تعديل
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Current Admins (6 cols) */}
          <div className="lg:col-span-6 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--divider)] pb-3">
              <h3 className="font-extrabold text-[var(--foreground)] text-base">
                المشرفون الحاليون
              </h3>

              <button
                onClick={() => setShowInviteModal(true)}
                className="px-3.5 py-1.5 bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs rounded-full border border-teal-600 transition-colors flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>دعوة مشرف جديد</span>
              </button>
            </div>

            <div className="divide-y divide-[var(--divider)] space-y-3">
              {adminsList.map((admin) => (
                <div
                  key={admin.id}
                  className="pt-3 first:pt-0 flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs ${admin.avatarColor}`}
                    >
                      <User className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="font-bold text-[var(--foreground)] text-sm">
                        {admin.name}
                      </h4>
                      <p className="text-xs text-[var(--text-subtle)] font-medium">
                        {admin.roleName} • {admin.timeAgo}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs font-bold">
                    <button
                      onClick={() => showToast(`تغيير دور المشرف ${admin.name}`, 'info')}
                      className="px-2.5 py-1 text-[var(--text-muted)] hover:text-[var(--foreground)] bg-[var(--card-hover)] hover:bg-[var(--badge-bg-muted)] rounded-lg border border-[var(--card-border)] transition-colors cursor-pointer"
                    >
                      تعديل
                    </button>
                    <button
                      onClick={() => setAdminToDelete(admin)}
                      className="px-2.5 py-1 text-rose-500 hover:text-rose-700 bg-rose-50 dark:bg-rose-500/10 hover:bg-rose-100 rounded-lg border border-rose-200 dark:border-rose-500/20 transition-colors cursor-pointer"
                    >
                      حذف
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Section: Permissions Matrix */}
        <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
          <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
            مصفوفة الصلاحيات (انقر للتعديل المباشر)
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-[var(--table-header-bg)] text-[var(--text-muted)] text-xs font-bold border-b border-[var(--card-border)]">
                  <th className="py-3 px-6">الإجراء</th>
                  <th className="py-3 px-4 text-center">مالك النظام</th>
                  <th className="py-3 px-4 text-center">مشرف رئيسي</th>
                  <th className="py-3 px-4 text-center">مراجع KYC</th>
                  <th className="py-3 px-4 text-center">مراجع عقارات</th>
                  <th className="py-3 px-4 text-center">دعم</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--divider)] text-xs">
                {matrix.map((row, idx) => (
                  <tr key={idx} className="hover:bg-[var(--table-row-hover)] transition-colors">
                    <td className="py-4 px-6 font-bold text-[var(--foreground)]">
                      {row.action}
                    </td>

                    <td
                      onClick={() => toggleMatrixCell(idx, 'systemOwner')}
                      className="py-4 px-4 text-center cursor-pointer hover:bg-teal-500/10 transition-colors rounded-lg"
                    >
                      {row.systemOwner ? (
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mx-auto" />
                      )}
                    </td>

                    <td
                      onClick={() => toggleMatrixCell(idx, 'mainAdmin')}
                      className="py-4 px-4 text-center cursor-pointer hover:bg-teal-500/10 transition-colors rounded-lg"
                    >
                      {row.mainAdmin ? (
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mx-auto" />
                      )}
                    </td>

                    <td
                      onClick={() => toggleMatrixCell(idx, 'kycReviewer')}
                      className="py-4 px-4 text-center cursor-pointer hover:bg-teal-500/10 transition-colors rounded-lg"
                    >
                      {row.kycReviewer ? (
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mx-auto" />
                      )}
                    </td>

                    <td
                      onClick={() => toggleMatrixCell(idx, 'propertyReviewer')}
                      className="py-4 px-4 text-center cursor-pointer hover:bg-teal-500/10 transition-colors rounded-lg"
                    >
                      {row.propertyReviewer ? (
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mx-auto" />
                      )}
                    </td>

                    <td
                      onClick={() => toggleMatrixCell(idx, 'support')}
                      className="py-4 px-4 text-center cursor-pointer hover:bg-teal-500/10 transition-colors rounded-lg"
                    >
                      {row.support ? (
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 dark:text-slate-600 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Invite Admin Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-md bg-[var(--card-bg)] border border-[var(--card-border)] rounded-2xl shadow-2xl p-6 space-y-4 text-right animate-scaleIn">
            <h3 className="font-extrabold text-base text-[var(--foreground)]">دعوة مشرف جديد</h3>
            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-[var(--text-subtle)] block mb-1">اسم المشرف</label>
                <input
                  type="text"
                  value={newAdminName}
                  onChange={(e) => setNewAdminName(e.target.value)}
                  placeholder="مثال: خالد عبدالرحمن"
                  className="w-full p-2.5 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl text-xs text-[var(--foreground)]"
                />
              </div>
              <div>
                <label className="font-bold text-[var(--text-subtle)] block mb-1">الدور المخصص</label>
                <select
                  value={newAdminRole}
                  onChange={(e) => setNewAdminRole(e.target.value)}
                  className="w-full p-2.5 bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl text-xs text-[var(--foreground)]"
                >
                  <option value="مشرف رئيسي">مشرف رئيسي</option>
                  <option value="مراجع KYC">مراجع KYC</option>
                  <option value="مراجع عقارات">مراجع عقارات</option>
                  <option value="دعم العملاء">دعم العملاء</option>
                </select>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--divider)]">
              <button
                onClick={() => setShowInviteModal(false)}
                className="px-4 py-2 bg-[var(--badge-bg-muted)] text-[var(--foreground)] text-xs font-bold rounded-xl"
              >
                إلغاء
              </button>
              <button
                onClick={handleInviteAdmin}
                className="px-5 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold rounded-xl"
              >
                إرسال الدعوة
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Admin Confirm Modal */}
      <ConfirmModal
        isOpen={!!adminToDelete}
        onClose={() => setAdminToDelete(null)}
        onConfirm={handleDeleteAdmin}
        title={`حذف المشرف ${adminToDelete?.name}`}
        message="هل أنت تأكد من رغبتك في سحب صلاحيات هذا المشرف وإزالته من لوحة التحكم؟"
        variant="danger"
        confirmText="تأكيد الحذف"
      />
    </div>
  );
}

