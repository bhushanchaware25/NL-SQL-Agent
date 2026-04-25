import { create } from 'zustand'

const useQueryStore = create((set, get) => ({
  // Connection state
  dbUrl: '',
  isConnected: false,
  connectedTableCount: 0,
  setDbUrl: (url) => set({ dbUrl: url }),
  setConnected: (val, tableCount = 0) => set({ isConnected: val, connectedTableCount: tableCount }),

  // Query state
  isLoading: false,
  question: '',
  setQuestion: (q) => set({ question: q }),

  // Agent trace
  agentSteps: [],
  addAgentStep: (step) => set((s) => ({ agentSteps: [...s.agentSteps, step] })),
  clearAgentSteps: () => set({ agentSteps: [] }),

  // Result
  result: null,  // { answer, sql, sqlExplanation, rows, rowCount, chartType, chartData, retryCount }
  setResult: (r) => set({ result: r }),

  // Query history
  history: [],
  addToHistory: (entry) =>
    set((s) => ({
      history: [entry, ...s.history].slice(0, 20),
    })),

  // Active tab in results panel
  activeTab: 'answer',
  setActiveTab: (tab) => set({ activeTab: tab }),

  // Sidebar open
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  // Reset for new query
  resetQuery: () =>
    set({
      isLoading: true,
      agentSteps: [],
      result: null,
      activeTab: 'answer',
    }),

  finishQuery: () => set({ isLoading: false }),
}))

export default useQueryStore
