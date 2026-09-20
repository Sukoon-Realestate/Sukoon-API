'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Plus } from 'lucide-react';

export default function PlatformSettingsPage() {
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
  const [admins, setAdmins] = useState([
    { id: '1', name: 'أحمد العدل', role: 'مشرف رئيسي', badge: 'مالك', badgeColor: 'bg-emerald-100 text-emerald-800' },
    { id: '2', name: 'سلمى رشدي', role: 'مراجع KYC', badge: 'مراجع', badgeColor: 'bg-teal-100 text-teal-800' },
  ]);

  const handleRemoveAdmin = (id: string) => {
    setAdmins((prev) => prev.filter((a) => a.id !== id));
  };

  const handleAddAdmin = () => {
    const newName = prompt('أدخل اسم المشرف الجديد:');
    if (!newName) return;
    setAdmins((prev) => [
      ...prev,
      {
        id: `admin-${Date.now()}`,
        name: newName,
        role: 'مراجع جديد',
        badge: 'مراجع',
        badgeColor: 'bg-teal-100 text-teal-800',
      },
    ]);
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إعدادات المنصة"
        subtitle="شروط التوثيق، ضوابط العقارات وتعيين المشرفين"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Grid: Verification & Property Settings */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Verification Settings (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
              إعدادات التوثيق
            </h3>

            <div className="space-y-4 text-xs">
              {/* Item 1 */}
              <div className="flex items-center justify-between py-1">
                <span className="font-bold text-slate-700">
                  مدة المراجعة القصوى (ساعات)
                </span>
                <button
                  type="button"
                  onClick={() => setMaxReviewHours(!maxReviewHours)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    maxReviewHours ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      maxReviewHours ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 2 */}
              <div className="flex items-center justify-between py-1 border-t border-slate-100 pt-3">
                <span className="font-bold text-slate-700">
                  مستندات مطلوبة للمستأجر
                </span>
                <button
                  type="button"
                  onClick={() => setTenantDocsRequired(!tenantDocsRequired)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    tenantDocsRequired ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      tenantDocsRequired ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 3 */}
              <div className="flex items-center justify-between py-1 border-t border-slate-100 pt-3">
                <span className="font-bold text-slate-700">
                  مستندات مطلوبة للمالك
                </span>
                <button
                  type="button"
                  onClick={() => setLandlordDocsRequired(!landlordDocsRequired)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    landlordDocsRequired ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      landlordDocsRequired ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 4 */}
              <div className="flex items-center justify-between py-1 border-t border-slate-100 pt-3">
                <span className="font-bold text-slate-700">
                  تفعيل التوثيق الآلي
                </span>
                <button
                  type="button"
                  onClick={() => setAutoVerification(!autoVerification)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    autoVerification ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      autoVerification ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Property Settings (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
              إعدادات العقارات
            </h3>

            <div className="space-y-4 text-xs">
              {/* Item 1 */}
              <div className="flex items-center justify-between py-1">
                <span className="font-bold text-slate-700">
                  الحد الأقصى للصور
                </span>
                <button
                  type="button"
                  onClick={() => setMaxPhotosLimit(!maxPhotosLimit)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    maxPhotosLimit ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      maxPhotosLimit ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 2 */}
              <div className="flex items-center justify-between py-1 border-t border-slate-100 pt-3">
                <span className="font-bold text-slate-700">
                  مدة المراجعة (أيام)
                </span>
                <button
                  type="button"
                  onClick={() => setReviewPeriodDays(!reviewPeriodDays)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    reviewPeriodDays ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      reviewPeriodDays ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 3 */}
              <div className="flex items-center justify-between py-1 border-t border-slate-100 pt-3">
                <span className="font-bold text-slate-700">
                  تفعيل الموقع التقريبي
                </span>
                <button
                  type="button"
                  onClick={() => setApproxLocation(!approxLocation)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    approxLocation ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      approxLocation ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>

              {/* Item 4 */}
              <div className="flex items-center justify-between py-1 border-t border-slate-100 pt-3">
                <span className="font-bold text-slate-700">
                  إخفاء الأرقام افتراضياً
                </span>
                <button
                  type="button"
                  onClick={() => setHidePhoneDefault(!hidePhoneDefault)}
                  className={`w-11 h-6 rounded-full transition-colors relative p-0.5 ${
                    hidePhoneDefault ? 'bg-[#0D7C66]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`w-5 h-5 rounded-full bg-white shadow-xs transition-transform ${
                      hidePhoneDefault ? 'translate-x-[-18px]' : 'translate-x-0'
                    }`}
                  ></div>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Admins Management */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
          <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
            إدارة المشرفين
          </h3>

          <div className="space-y-3">
            {admins.map((adm) => (
              <div
                key={adm.id}
                className="flex items-center justify-between border-b border-slate-100 pb-3"
              >
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">
                    {adm.name}
                  </h4>
                  <p className="text-xs text-slate-400 font-medium">
                    {adm.role}
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold ${adm.badgeColor}`}
                  >
                    {adm.badge}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveAdmin(adm.id)}
                    className="px-3 py-1 bg-rose-50 hover:bg-rose-100 text-rose-600 font-bold text-xs rounded-lg border border-rose-100 transition-colors"
                  >
                    حذف
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={handleAddAdmin}
              className="w-full sm:w-auto px-6 py-3.5 bg-teal-50/80 hover:bg-teal-100 text-[#0D7C66] font-extrabold text-xs rounded-xl border border-teal-100 transition-colors flex items-center justify-center gap-2"
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
