'use client';

import React from 'react';
import { Header } from '@/components/layout/Header';
import { Plus, User, Check, X } from 'lucide-react';
import {
  mockAdminRoles,
  mockAdminUsers,
  mockPermissionsMatrix,
} from '@/data/mockData';

export default function AdminRolesPage() {
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
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
              الأدوار والصلاحيات
            </h3>

            <div className="space-y-3">
              {mockAdminRoles.map((role) => (
                <div
                  key={role.id}
                  className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 hover:border-slate-200 transition-all flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${role.color}`}></span>
                      <h4 className="font-bold text-slate-900 text-sm">
                        {role.name}
                      </h4>
                    </div>
                    {role.subtext && (
                      <p className="text-xs text-slate-400 font-medium">
                        {role.subtext}
                      </p>
                    )}
                    {role.badges && role.badges.length > 0 && (
                      <div className="flex items-center gap-1.5 pt-1">
                        {role.badges.map((badge, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200/60"
                          >
                            {badge}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <div className="text-center px-2">
                      <span className="font-extrabold text-slate-900 text-sm block leading-none">
                        {role.userCount}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">
                        مستخدم
                      </span>
                    </div>

                    <button className="px-3 py-1 bg-slate-100 hover:bg-slate-200/80 text-slate-700 font-bold rounded-lg border border-slate-200/80 transition-colors text-xs">
                      تعديل
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Current Admins (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-slate-800 text-base">
                المشرفون الحاليون
              </h3>

              <button className="px-3 py-1.5 bg-teal-50 hover:bg-teal-100 text-[#0D7C66] font-bold text-xs rounded-full border border-teal-100 transition-colors flex items-center gap-1">
                <Plus className="w-3.5 h-3.5" />
                <span>دعوة مشرف</span>
              </button>
            </div>

            <div className="divide-y divide-slate-100 space-y-3">
              {mockAdminUsers.map((admin) => (
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
                      <h4 className="font-bold text-slate-900 text-sm">
                        {admin.name}
                      </h4>
                      <p className="text-xs text-slate-400 font-medium">
                        {admin.roleName} • {admin.timeAgo}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs font-bold">
                    <button className="px-2.5 py-1 text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200/60 transition-colors">
                      تعديل الدور
                    </button>
                    <button className="px-2.5 py-1 text-rose-500 hover:text-rose-700 bg-rose-50 hover:bg-rose-100/80 rounded-lg border border-rose-100 transition-colors">
                      حذف
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Section: Permissions Matrix */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
          <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
            مصفوفة الصلاحيات
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-slate-50/80 text-slate-500 text-xs font-bold border-b border-slate-200/80">
                  <th className="py-3 px-6">الإجراء</th>
                  <th className="py-3 px-4 text-center">مالك النظام</th>
                  <th className="py-3 px-4 text-center">مشرف رئيسي</th>
                  <th className="py-3 px-4 text-center">مراجع KYC</th>
                  <th className="py-3 px-4 text-center">مراجع عقارات</th>
                  <th className="py-3 px-4 text-center">دعم</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {mockPermissionsMatrix.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                    <td className="py-4 px-6 font-bold text-slate-800">
                      {row.action}
                    </td>

                    <td className="py-4 px-4 text-center">
                      {row.systemOwner ? (
                        <Check className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 mx-auto" />
                      )}
                    </td>

                    <td className="py-4 px-4 text-center">
                      {row.mainAdmin ? (
                        <Check className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 mx-auto" />
                      )}
                    </td>

                    <td className="py-4 px-4 text-center">
                      {row.kycReviewer ? (
                        <Check className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 mx-auto" />
                      )}
                    </td>

                    <td className="py-4 px-4 text-center">
                      {row.propertyReviewer ? (
                        <Check className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 mx-auto" />
                      )}
                    </td>

                    <td className="py-4 px-4 text-center">
                      {row.support ? (
                        <Check className="w-4 h-4 text-emerald-600 mx-auto" />
                      ) : (
                        <X className="w-4 h-4 text-slate-300 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
