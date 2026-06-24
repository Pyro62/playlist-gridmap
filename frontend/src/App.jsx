import { useState } from 'react'

function App() {
  const [songData, setSongData] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchSkeletonMap = async () => {
    setLoading(true)
    try {
      // Because of vercel.json, this automatically maps to your Render backend!
      const response = await fetch('/api/')
      const data = await response.json()
      setSongData(data)
    } catch (error) {
      console.error("Error fetching map:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', textAlign: 'center' }}>
      <h1>🎵 Spotify Visualizer Walking Skeleton 🎵</h1>
      <button 
        onClick={fetchSkeletonMap} 
        disabled={loading}
        style={{ padding: '12px 24px', fontSize: '16px', cursor: 'pointer' }}
      >
        {loading ? 'Waking up Render backend...' : 'Test Backend Connection'}
      </button>

      {songData && (
        <div style={{ marginTop: '30px', textAlign: 'left', display: 'inline-block', background: '#f5f5f5', padding: '20px', borderRadius: '8px' }}>
          <h3>Data Received from Render &lt;=&gt; Vercel:</h3>
          <pre>{JSON.stringify(songData, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default App