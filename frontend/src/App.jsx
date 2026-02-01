import React, { useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './components/Login'
import TodoApp from './components/TodoApp'
import './App.css'

function AppContent() {
  const { user, loading, login } = useAuth()

  useEffect(() => {
    // Check for token in URL (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search)
    const token = urlParams.get('token')
    
    if (token) {
      login(token)
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading...</div>
      </div>
    )
  }

  return (
    <div className="App">
      {user ? <TodoApp /> : <Login />}
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App