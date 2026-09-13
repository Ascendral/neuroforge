'use client';

import { type ReactNode, useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  borderColor?: string; // kept for call-site compatibility; unused in the glass look
  rightSlot?: ReactNode;
  children: ReactNode;
}

export function CollapsibleSection({
  title,
  subtitle,
  defaultOpen = false,
  rightSlot,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="float-panel overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="press flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
      >
        <span className="flex items-baseline gap-2">
          <span
            className="inline-block w-3 text-[10px] text-white/40"
            style={{
              transform: open ? 'rotate(90deg)' : 'none',
              transition: 'transform 0.3s var(--spring)',
            }}
          >
            ▸
          </span>
          <span className="meta text-white/80">{title}</span>
          {subtitle && <span className="meta-xs">{subtitle}</span>}
        </span>
        {rightSlot}
      </button>
      {open && <div className="rise space-y-3 px-4 pb-4 pt-1 text-[13px]">{children}</div>}
    </div>
  );
}
