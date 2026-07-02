import { useState } from 'react'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState(localStorage.getItem('token'))

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

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  return (
    <div style={{ padding: '12px', fontFamily: 'sans-serif', textAlign: 'center' }}>
      <h1>music gridmap</h1>

      <button onClick={check} disabled={loading}>
        {loading ? 'Checking...' : 'Sanity Check'}
      </button>

      {token ? (
        <>
          <p style={{ color: 'green' }}>Logged in</p>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <button onClick={() => window.location.href = '/api/auth/login'}>
          Login with Spotify
        </button>
      )}

      {result && (
        <p style={{ marginTop: '20px', color: result.success ? 'green' : 'red' }}>
          {result.success ? JSON.stringify(result.data) : `Error: ${result.error}`}
        </p>
      )}
    </div>
  )
}

export default App