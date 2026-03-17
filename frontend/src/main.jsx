import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import OptIn from './components/OptIn'
import './index.css'

const isOptIn = window.location.pathname === '/opt-in'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isOptIn ? <OptIn /> : <App />}
  </React.StrictMode>
)
