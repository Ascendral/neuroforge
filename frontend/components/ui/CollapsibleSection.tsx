'use client';

import { type ReactNode, useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  borderColor?: string;
  rightSlot?: ReactNode;
  children: ReactNode;
}

export function CollapsibleSection({
  title,
  subtitle,
  defaultOpen = false,
  borderColor = 'border-white/10',
  rightSlot,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={`rounded border ${borderColor} bg-black/85`}>
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-baseline justify-between gap-2 px-3 py-2 text-left hover:bg-white/5"
      >
        <span className="flex items-baseline gap-2">
          <span className="inline-block w-3 text-[10px] text-white/40">{open ? '▾' : '▸'}</span>
          <span className="text-[10px] font-mono uppercase tracking-widest text-white/60">
            {title}
          </span>
          {subtitle && <span className="font-mono text-[10px] text-white/30">{subtitle}</span>}
        </span>
        {rightSlot}
      </button>
      {open && <div className="space-y-2 px-3 pb-3 pt-1">{children}</div>}
    </div>
  );
}
