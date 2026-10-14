import type { ReactNode } from "react";

export function IPhoneFrame({ children }: { children: ReactNode }) {
  return (
    <div className="relative mx-auto w-full max-w-[260px] sm:max-w-[280px]" data-iphone-frame>
      <span aria-hidden className="absolute -left-[3px] top-[17%] h-[4%] w-[3px] rounded-l-sm bg-[#59615b]" />
      <span aria-hidden className="absolute -left-[3px] top-[25%] h-[8%] w-[3px] rounded-l-sm bg-[#59615b]" />
      <span aria-hidden className="absolute -left-[3px] top-[35%] h-[8%] w-[3px] rounded-l-sm bg-[#59615b]" />
      <span aria-hidden className="absolute -right-[3px] top-[28%] h-[12%] w-[3px] rounded-r-sm bg-[#59615b]" />
      <div className="rounded-[2.65rem] bg-linear-to-b from-[#68716a] via-[#252d28] to-[#465149] p-[3px] shadow-[0_30px_60px_-18px_rgba(0,0,0,0.5)]">
        <div className="rounded-[2.45rem] bg-black p-[5px]">
          <div className="overflow-hidden rounded-[2.15rem] bg-paper">{children}</div>
        </div>
      </div>
    </div>
  );
}
