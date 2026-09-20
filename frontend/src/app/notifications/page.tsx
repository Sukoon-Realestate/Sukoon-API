'use client';

import React, { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { mockPushCampaigns } from '@/data/mockData';

export default function PushNotificationsPage() {
  const [audience, setAudience] = useState<'all' | 'tenants' | 'landlords' | 'verified'>('all');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [campaigns, setCampaigns] = useState(mockPushCampaigns);

  const handleSendNow = () => {
    if (!title.trim() || !body.trim()) return;
    setCampaigns((prev) => [
      {
        id: `nc-${Date.now()}`,
        title,
        timeAgo: 'الآن',
        body,
        openRate: '0% فتح',
        recipientCount: '2,847 وصل',
      },
      ...prev,
    ]);
    setTitle('');
    setBody('');
  };

  return (
    <div className="flex-1 flex flex-col pb-12">
      <Header
        title="إدارة الإشعارات المدفوعة"
        subtitle="إنشاء حملات الإشعارات، الاستهداف وفحص معدلات الفتح والتفاعل"
        lastUpdated="9:41 ص"
      />

      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Create Notification Form (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
            <h3 className="font-extrabold text-slate-800 text-base border-b border-slate-100 pb-3">
              إرسال إشعار جديد
            </h3>

            {/* Target Audience */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400">
                الجمهور المستهدف
              </label>
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                <button
                  type="button"
                  onClick={() => setAudience('all')}
                  className={`px-4 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                    audience === 'all'
                      ? 'bg-[#0D7C66] text-white shadow-xs'
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  كل المستخدمين
                </button>
                <button
                  type="button"
                  onClick={() => setAudience('tenants')}
                  className={`px-4 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                    audience === 'tenants'
                      ? 'bg-[#0D7C66] text-white shadow-xs'
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  مستأجرون
                </button>
                <button
                  type="button"
                  onClick={() => setAudience('landlords')}
                  className={`px-4 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                    audience === 'landlords'
                      ? 'bg-[#0D7C66] text-white shadow-xs'
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  ملاك
                </button>
                <button
                  type="button"
                  onClick={() => setAudience('verified')}
                  className={`px-4 py-2 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                    audience === 'verified'
                      ? 'bg-[#0D7C66] text-white shadow-xs'
                      : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                  }`}
                >
                  موثّقون فقط
                </button>
              </div>
            </div>

            {/* Notification Title Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400">
                عنوان الإشعار
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="مثال: عروض الصيف على سكون!"
                className="w-full p-3 bg-slate-50/70 border border-slate-200/80 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-[#0D7C66] placeholder:text-slate-400"
              />
            </div>

            {/* Notification Body Textarea */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-400">
                نص الإشعار
              </label>
              <textarea
                rows={4}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="نص الإشعار..."
                className="w-full p-3 bg-slate-50/70 border border-slate-200/80 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-[#0D7C66] placeholder:text-slate-400 resize-none"
              ></textarea>
            </div>

            {/* Form Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <button
                type="button"
                onClick={handleSendNow}
                className="py-3.5 bg-[#0D7C66] hover:bg-[#0B6856] text-white font-extrabold text-sm rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2"
              >
                <span>إرسال الآن</span>
              </button>

              <button
                type="button"
                className="py-3.5 bg-slate-50 hover:bg-slate-100 text-slate-700 font-extrabold text-sm rounded-xl border border-slate-200/80 transition-colors flex items-center justify-center gap-2"
              >
                <span>جدولة</span>
              </button>
            </div>
          </div>

          {/* Right Column: Sent Notifications History (6 cols) */}
          <div className="lg:col-span-6 bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs space-y-5">
            <h3 className="font-black text-slate-800 text-base border-b border-slate-100 pb-3">
              سجل الإشعارات المرسلة
            </h3>

            <div className="divide-y divide-slate-100 space-y-4">
              {campaigns.map((camp) => (
                <div key={camp.id} className="pt-4 first:pt-0 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <h4 className="font-extrabold text-slate-900 text-sm">
                      {camp.title}
                    </h4>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {camp.timeAgo}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 font-medium leading-relaxed">
                    {camp.body}
                  </p>

                  <div className="flex items-center gap-3 text-xs font-bold pt-1">
                    <span className="text-emerald-500">{camp.openRate}</span>
                    <span className="text-slate-400 font-normal">{camp.recipientCount}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
