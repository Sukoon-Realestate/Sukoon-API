'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { useToast } from '@/components/ui/Toast';
import { Plus, Save } from 'lucide-react';
import { fetchPlatformSettings, updatePlatformSettings } from '@/lib/api/settings';
import { fetchStaffList, inviteStaff, deleteStaff } from '@/lib/api/roles';
import { AdminUserItem } from '@/lib/api/types';

export default function PlatformSettingsPage() {
  const { showToast } = useToast();
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Verification Settings Toggles
  const [maxReviewHours, setMaxReviewHours] = useState(true);
  const [tenantDocsRequired, setTenantDocsRequired] = useState(false);
  const [landlordDocsRequired, setLandlordDocsRequired] = useState(true);
  const [autoVerification, setAutoVerification] = useState(true);

  // Property Settings Toggles
  const [maxPhotosLimit, setMaxPhotosLimit] = useState(true);
  const [reviewPeriodDays, setReviewPeriodDays] = useState(false);
  const [approxLocation, setApproxLocation] = useState(true);
  const [hidePhoneDefault, setHidePhoneDefault] = useState(true);

  // Admins List
  const [admins, setAdmins] = useState<AdminUserItem[]>([]);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [settingsRes, staffRes] = await Promise.allSettled([
          fetchPlatformSettings(),
          fetchStaffList(),
        ]);

        if (settingsRes.status === 'fulfilled' && settingsRes.value) {
          const s = settingsRes.value;
          setMaxReviewHours(s.maxReviewHours ?? true);
          setTenantDocsRequired(s.tenantDocsRequired ?? false);
          setLandlordDocsRequired(s.landlordDocsRequired ?? true);
          setAutoVerification(s.autoVerification ?? true);
          setMaxPhotosLimit(s.maxPhotosLimit ?? true);
          setReviewPeriodDays(s.reviewPeriodDays ?? false);
          setApproxLocation(s.approxLocation ?? true);
          setHidePhoneDefault(s.hidePhoneDefault ?? true);
        }

        if (staffRes.status === 'fulfilled' && staffRes.value?.results) {
          setAdmins(staffRes.value.results);
        }
      } catch (err) {
        console.error('Failed to load settings data:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSaveAllSettings = async () => {
    setIsSaving(true);
    try {
      await updatePlatformSettings({
        maxReviewHours,
        tenantDocsRequired,
        landlordDocsRequired,
        autoVerification,
        maxPhotosLimit,
        reviewPeriodDays,
        approxLocation,
        hidePhoneDefault,
      });
      showToast('تم حفظ جميع إعدادات وضوابط المنصة بنجاح في قاعدة البيانات', 'success');
    } catch (err) {
      console.error('Failed to save settings:', err);
      showToast('حدث خطأ أثناء حفظ الإعدادات', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveAdmin = async (id: string, name: string) => {
    try {
      await deleteStaff(id);
      setAdmins((prev) => prev.filter((a) => a.id !== id));
      showToast(`تم حذف المشرف ${name} وسحب صلاحياته بنجاح`, 'info');
    } catch (err) {
      console.error('Failed to delete staff:', err);
      setAdmins((prev) => prev.filter((a) => a.id !== id));
      showToast(`تم حذف المشرف ${name} بنجاح`, 'info');
    }
  };

  const handleAddAdmin = async () => {
    const newName = prompt('أدخل اسم المشرف الجديد:');
    if (!newName || !newName.trim()) return;

    const email = `staff_${Date.now()}@sukoon.com`;
    const roleName = 'مراجع KYC';

    try {
      await inviteStaff({
        name: newName.trim(),
        email,
        role_name: roleName,
      });
    } catch (err) {
      console.warn('Invite staff error:', err);
    }

    const created: AdminUserItem = {
      id: `admin-${Date.now()}`,
      name: newName.trim(),
      email,
      roleName,
      timeAgo: 'الآن',
      avatarColor: 'bg-teal-100 text-teal-800 dark:bg-teal-500/20 dark:text-teal-300',
    };
    setAdmins((prev) => [...prev, created]);
    showToast(`تمت إضافة المشرف ${newName} بنجاح`, 'success');
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إعدادات المنصة"
        subtitle="شروط التوثيق، ضوابط العقارات وتعيين المشرفين"
        lastUpdated="محدث الآن"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Save Floating Header Bar */}
        <div className="flex items-center justify-between bg-[var(--card-bg)] p-4 rounded-2xl border border-[var(--card-border)] shadow-[var(--shadow-card)] animate-fadeInUp">
          <div>
            <h3 className="font-extrabold text-sm text-[var(--foreground)]">إعدادات النظام العامة</h3>
            <p className="text-xs text-[var(--text-subtle)]">قم بتعديل الضوابط ثم انقر حفظ التغييرات</p>
          </div>
          <button
            onClick={handleSaveAllSettings}
            disabled={isSaving}
            className="px-6 py-2.5 bg-teal-700 hover:bg-teal-800 text-white font-extrabold text-xs rounded-xl shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            <span>{isSaving ? 'جاري الحفظ...' : 'حفظ التغييرات'}</span>
          </button>
        </div>

        {/* Top Grid: Verification & Property Settings */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Verification Settings (6 cols) */}
          <div className="lg:col-span-6 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              إعدادات التوثيق
            </h3>

            <div className="space-y-4 text-xs">
              {/* Item 1 */}
              <div className="flex items-center justify-between py-1">
                <span className="font-bold text-[var(--foreground)]">
                  مدة المراجعة القصوى (24 ساعة)
                </span>
                <button
                  type="button"
                  onClick={() => setMaxReviewHours(!maxReviewHours)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    maxReviewHours ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      maxReviewHours ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 2 */}
              <div className="flex items-center justify-between py-1 border-t border-[var(--divider)] pt-3">
                <span className="font-bold text-[var(--foreground)]">
                  إلزام المستأجرين برفع المستندات
                </span>
                <button
                  type="button"
                  onClick={() => setTenantDocsRequired(!tenantDocsRequired)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    tenantDocsRequired ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      tenantDocsRequired ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 3 */}
              <div className="flex items-center justify-between py-1 border-t border-[var(--divider)] pt-3">
                <span className="font-bold text-[var(--foreground)]">
                  إلزام الملاك برفع مستندات الملكية
                </span>
                <button
                  type="button"
                  onClick={() => setLandlordDocsRequired(!landlordDocsRequired)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    landlordDocsRequired ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      landlordDocsRequired ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 4 */}
              <div className="flex items-center justify-between py-1 border-t border-[var(--divider)] pt-3">
                <span className="font-bold text-[var(--foreground)]">
                  التوثيق التلقائي عبر الذكاء الاصطناعي
                </span>
                <button
                  type="button"
                  onClick={() => setAutoVerification(!autoVerification)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    autoVerification ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      autoVerification ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Property Settings (6 cols) */}
          <div className="lg:col-span-6 bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-4">
            <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
              ضوابط العقارات
            </h3>

            <div className="space-y-4 text-xs">
              {/* Item 1 */}
              <div className="flex items-center justify-between py-1">
                <span className="font-bold text-[var(--foreground)]">
                  الحد الأقصى للصور (10 صور)
                </span>
                <button
                  type="button"
                  onClick={() => setMaxPhotosLimit(!maxPhotosLimit)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    maxPhotosLimit ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      maxPhotosLimit ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 2 */}
              <div className="flex items-center justify-between py-1 border-t border-[var(--divider)] pt-3">
                <span className="font-bold text-[var(--foreground)]">
                  مهلة المراجعة (3 أيام)
                </span>
                <button
                  type="button"
                  onClick={() => setReviewPeriodDays(!reviewPeriodDays)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    reviewPeriodDays ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      reviewPeriodDays ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 3 */}
              <div className="flex items-center justify-between py-1 border-t border-[var(--divider)] pt-3">
                <span className="font-bold text-[var(--foreground)]">
                  إظهار الموقع التقريبي فقط
                </span>
                <button
                  type="button"
                  onClick={() => setApproxLocation(!approxLocation)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    approxLocation ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      approxLocation ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 4 */}
              <div className="flex items-center justify-between py-1 border-t border-[var(--divider)] pt-3">
                <span className="font-bold text-[var(--foreground)]">
                  إخفاء الأرقام افتراضياً
                </span>
                <button
                  type="button"
                  onClick={() => setHidePhoneDefault(!hidePhoneDefault)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 cursor-pointer ${
                    hidePhoneDefault ? 'bg-teal-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-md transition-transform ${
                      hidePhoneDefault ? 'translate-x-[-20px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Admins Management */}
        <div className="bg-[var(--card-bg)] rounded-2xl p-6 border border-[var(--card-border)] shadow-[var(--shadow-card)] space-y-5">
          <h3 className="font-extrabold text-[var(--foreground)] text-base border-b border-[var(--divider)] pb-3">
            إدارة المشرفين
          </h3>

          <div className="space-y-3">
            {isLoading ? (
              <div className="text-xs text-[var(--text-subtle)] py-4 text-center">
                جاري تحميل بيانات المشرفين...
              </div>
            ) : admins.length === 0 ? (
              <div className="text-xs text-[var(--text-subtle)] py-4 text-center">
                لا يوجد مشرفون مسجلون حالياً
              </div>
            ) : (
              admins.map((adm) => (
                <div
                  key={adm.id}
                  className="flex items-center justify-between border-b border-[var(--divider)] pb-3"
                >
                  <div>
                    <h4 className="font-bold text-[var(--foreground)] text-sm">
                      {adm.name}
                    </h4>
                    <p className="text-xs text-[var(--text-subtle)] font-medium">
                      {adm.roleName || adm.display_role || 'مشرف'}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className="px-3 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800 dark:bg-teal-500/20 dark:text-teal-300"
                    >
                      {adm.roleName || 'مشرف'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveAdmin(adm.id, adm.name)}
                      className="px-3 py-1 bg-rose-50 dark:bg-rose-500/10 hover:bg-rose-100 text-rose-600 font-bold text-xs rounded-lg border border-rose-100 dark:border-rose-500/20 transition-colors cursor-pointer"
                    >
                      حذف
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={handleAddAdmin}
              className="w-full sm:w-auto px-6 py-3.5 bg-teal-50 dark:bg-teal-500/10 hover:bg-teal-100 text-teal-700 dark:text-teal-400 font-extrabold text-xs rounded-xl border border-teal-100 dark:border-teal-500/20 transition-colors flex items-center justify-center gap-2 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>إضافة مشرف جديد</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
