import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function Callback() {
  const navigate = useNavigate()

  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get('code')
    
    fetch(`/api/auth/callback?code=${code}`)
      .then(res => res.json())
      .then(data => {
        localStorage.setItem('token', data.token)
        navigate('/')
      })
  }, [])

  return <p>Logging in...</p>
}

export default Callback