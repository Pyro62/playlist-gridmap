import { useState } from 'react'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [playlistUrl, setPlaylistUrl] = useState('')
  const [ingestResult, setIngestResult] = useState(null)
  const [ingesting, setIngesting] = useState(false)

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

  const ingestPlaylist = async () => {
    if (!playlistUrl.trim()) return
    setIngesting(true)
    try {
      const response = await fetch(
        `/api/playlist/ingest?playlist_id=${encodeURIComponent(playlistUrl)}`,
        { method: 'POST' }
      )
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Ingest failed')
      setIngestResult({ success: true, data })
    } catch (error) {
      setIngestResult({ success: false, error: error.message })
    } finally {
      setIngesting(false)
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

      <div style={{ marginTop: '20px' }}>
        <input
          type="text"
          value={playlistUrl}
          onChange={(e) => setPlaylistUrl(e.target.value)}
          placeholder="Spotify playlist URL"
          style={{ padding: '6px', width: '280px' }}
        />
        <button onClick={ingestPlaylist} disabled={ingesting} style={{ marginLeft: '8px' }}>
          {ingesting ? 'Ingesting...' : 'Ingest Playlist'}
        </button>
      </div>

      {ingestResult && (
        <p style={{ marginTop: '10px', color: ingestResult.success ? 'green' : 'red' }}>
          {ingestResult.success ? JSON.stringify(ingestResult.data) : `Error: ${ingestResult.error}`}
        </p>
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