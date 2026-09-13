// Section kicker: short red rule + tracked small caps. Web port of Motor Garage's Kicker.
export function Kicker({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`kicker ${className}`}>{children}</div>;
}

// Serif display line in wide-tracked capitals (the make across the car).
export function DisplayLine({
  children,
  size = 28,
  className = '',
}: {
  children: React.ReactNode;
  size?: number;
  className?: string;
}) {
  return (
    <div className={`display text-white ${className}`} style={{ fontSize: size }}>
      {children}
    </div>
  );
}

// Stat tile: red glyph, big value, small-caps label.
export function StatTile({
  label,
  value,
  glyph = '◆',
  sub,
}: {
  label: string;
  value: React.ReactNode;
  glyph?: string;
  sub?: React.ReactNode;
}) {
  return (
    <div className="glass tile flex flex-col gap-2 p-4">
      <span className="text-[14px] text-accent">{glyph}</span>
      <span className="serif text-[19px] leading-tight text-white">{value}</span>
      <span className="meta-xs">{label}</span>
      {sub && <span className="text-[11px] text-white/40">{sub}</span>}
    </div>
  );
}
