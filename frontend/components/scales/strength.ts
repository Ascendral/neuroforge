import type { EvidenceStrength } from '@/lib/types';

export const STRENGTH_COLOR: Record<EvidenceStrength, string> = {
  equivalence: '#ff2d2d',
  strong: '#ffffff',
  analogy: 'rgba(255,255,255,0.45)',
  none: 'rgba(255,255,255,0.22)',
};

export const STRENGTH_LABEL: Record<EvidenceStrength, string> = {
  equivalence: 'equivalence — proved same mathematics',
  strong: 'strong — quantitative / causal evidence',
  analogy: 'analogy — conceptual parallel only',
  none: 'none — no known counterpart',
};

export const STRENGTH_DASH: Record<EvidenceStrength, string | undefined> = {
  equivalence: undefined,
  strong: undefined,
  analogy: '4 3',
  none: '1 3',
};

export function bestStrength(strengths: EvidenceStrength[]): EvidenceStrength | null {
  const order: EvidenceStrength[] = ['equivalence', 'strong', 'analogy', 'none'];
  for (const s of order) if (strengths.includes(s)) return s;
  return null;
}
