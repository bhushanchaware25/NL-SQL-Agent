import { useRef, useCallback } from 'react'
import useQueryStore from '../store/queryStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/query'

export function useWebSocket() {
  const wsRef = useRef(null)
  const {
    resetQuery, finishQuery, addAgentStep, setResult, addToHistory, dbUrl
  } = useQueryStore()

  const sendQuery = useCallback((question) => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close()
    }

    resetQuery()

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({
        question,
        database_url: dbUrl || null,
      }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)

        if (msg.event === 'agent_step') {
          addAgentStep({
            agent: msg.agent,
            status: msg.status,
            message: msg.message,
            data: msg.data,
            timestamp: Date.now(),
          })
        } else if (msg.event === 'done') {
          const result = {
            answer: msg.answer,
            sql: msg.sql,
            sqlExplanation: msg.sql_explanation,
            rows: msg.rows || [],
            rowCount: msg.row_count || 0,
            chartType: msg.chart_type || null,
            chartData: msg.chart_data || null,
            retryCount: msg.retry_count || 0,
          }
          setResult(result)
          addToHistory({ question, result, timestamp: Date.now() })
          finishQuery()
        } else if (msg.event === 'error') {
          addAgentStep({
            agent: 'System',
            status: 'error',
            message: msg.message,
            timestamp: Date.now(),
          })
          finishQuery()
        }
      } catch (e) {
        console.error('WS parse error:', e)
        finishQuery()
      }
    }

    ws.onerror = () => {
      addAgentStep({
        agent: 'System',
        status: 'error',
        message: 'WebSocket connection failed. Is the backend running?',
        timestamp: Date.now(),
      })
      finishQuery()
    }

    // onclose: only finish if not already done (fallback for unexpected disconnects)
    ws.onclose = () => {
      // Use a small delay to let the last onmessage fire first
      setTimeout(() => finishQuery(), 100)
    }
  }, [dbUrl, resetQuery, finishQuery, addAgentStep, setResult, addToHistory])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  return { sendQuery, disconnect }
}
