'use client';

import { createContext, useContext } from 'react';

// Anti-theater note: this context only carries a setter for which neuron the
// 3D viewer should render. The actual neuron data (SWC points + metadata)
// always comes from a live /api/neurons/{id} fetch in page.tsx — there is
// no client-side cache of fake neurons keyed off this id.

export interface NeuronSelectionContext {
  selectNeuron: (id: number) => void;
  selectedId: number;
}

export const NeuronSelectionCtx = createContext<NeuronSelectionContext | null>(null);

export function useNeuronSelection(): NeuronSelectionContext | null {
  return useContext(NeuronSelectionCtx);
}
