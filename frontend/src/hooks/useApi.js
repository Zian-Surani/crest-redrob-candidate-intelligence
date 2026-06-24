import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api'

export function useApi(path, initialValue = null) {
  const [data, setData] = useState(initialValue)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const next = await api(path)
      setData(next)
      return next
    } catch (requestError) {
      setError(requestError.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [path])

  useEffect(() => {
    const timer = window.setTimeout(refresh, 0)
    return () => window.clearTimeout(timer)
  }, [refresh])
  return { data, setData, loading, error, refresh }
}
