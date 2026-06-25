import { create } from 'zustand'

interface UiState {
  selectedApplicationId: number | null
  setSelectedApplicationId: (id: number | null) => void
}

export const useUiStore = create<UiState>((set) => ({
  selectedApplicationId: null,
  setSelectedApplicationId: (id) => set({ selectedApplicationId: id }),
}))
