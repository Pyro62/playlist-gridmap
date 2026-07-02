import { useState } from 'react'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const check = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api')
      const data = await response.json()
      setResult({ success: true, data })
    } catch (error) {
      setResult({ success: false, error: error.message })
    } finally {
      setLoading(false)
    }
  }
  const login = async () => {
    window.location.href = '/api/auth/login'
  }

  return (
    <div style={{ padding: '12px', fontFamily: 'sans-serif', textAlign: 'center' }}>
      <h1>music gridmap</h1>
      <button onClick={check} disabled={loading}>
        {loading ? 'Checking...' : 'Sanity Check'}
      </button>

      <button onClick={login} disabled={loading}>
      {loading ? 'Loading': 'Login'}
      </button>

      {result && (
        <p style={{ marginTop: '20px', color: result.success ? 'green' : 'red' }}>
          {result.success ? JSON.stringify(result.data) : `Error: ${result.error}`}
        </p>
      )}
    </div>
  )
}

export default App