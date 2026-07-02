import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function Callback() {
  const navigate = useNavigate()

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const error = params.get('error')
    const code = params.get('code')

    if (error) {
      navigate('/')
      return
    }

    if (!code) {
      navigate('/')
      return
    }

    fetch(`/api/auth/callback?code=${code}`)
      .then(res => res.json())
      .then(data => {
        if (data.token) {
          localStorage.setItem('token', data.token)
          navigate('/')
        } else {
          navigate('/?error=login_failed')
        }
      })
      .catch(() => navigate('/'))
  }, [])

  return <p>Logging in...</p>
}

export default Callback