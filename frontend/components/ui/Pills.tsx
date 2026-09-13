'use client';

import { type ReactNode, useLayoutEffect, useRef, useState } from 'react';

// Pill segmented control: a glass capsule with a white fill that SLIDES to the
// chosen option. Web port of Motor Garage's PillSegmentedControl.

interface PillsProps<T extends string> {
  options: readonly T[];
  value: T;
  onChange: (v: T) => void;
  label?: (v: T) => ReactNode;
  fill?: boolean; // stretch to container width
  size?: 'sm' | 'md';
  className?: string;
}

export function Pills<T extends string>({
  options,
  value,
  onChange,
  label,
  fill = false,
  size = 'md',
  className = '',
}: PillsProps<T>) {
  const refs = useRef<Map<T, HTMLButtonElement>>(new Map());
  const wrap = useRef<HTMLDivElement | null>(null);
  const [ind, setInd] = useState<{ left: number; width: number } | null>(null);

  useLayoutEffect(() => {
    const el = refs.current.get(value);
    const w = wrap.current;
    if (!el || !w) return;
    const measure = () => {
      const a = el.getBoundingClientRect();
      const b = w.getBoundingClientRect();
      setInd({ left: a.left - b.left, width: a.width });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(w);
    return () => ro.disconnect();
  }, [value, options]);

  const pad = size === 'sm' ? 'px-3.5 py-1.5' : 'px-4 py-2.5';
  const fs = size === 'sm' ? 'text-[11.5px]' : 'text-[13px]';

  return (
    <div
      ref={wrap}
      className={`glass relative inline-flex rounded-full p-1 ${fill ? 'w-full' : ''} ${className}`}
    >
      {ind && (
        <span
          aria-hidden
          className="absolute top-1 bottom-1 rounded-full bg-white shadow-[0_6px_18px_rgba(0,0,0,0.45)]"
          style={{
            left: ind.left,
            width: ind.width,
            transition: 'left 0.38s var(--spring), width 0.38s var(--spring)',
          }}
        />
      )}
      {options.map((o) => {
        const on = o === value;
        return (
          <button
            key={o}
            ref={(el) => {
              if (el) refs.current.set(o, el);
              else refs.current.delete(o);
            }}
            onClick={() => onChange(o)}
            className={`press relative z-10 rounded-full ${pad} ${fs} font-semibold lowercase tracking-[0.1em] [font-variant:small-caps] whitespace-nowrap ${
              fill ? 'flex-1' : ''
            } ${on ? 'text-[#0A0A0B]' : 'text-white/55 hover:text-white'}`}
            style={{ transition: 'color 0.25s ease, transform 0.25s var(--spring)' }}
          >
            {label ? label(o) : o}
          </button>
        );
      })}
    </div>
  );
}
