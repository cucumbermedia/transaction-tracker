import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import OptIn from './components/OptIn'
import PrivacyPolicy from './components/PrivacyPolicy'
import Terms from './components/Terms'
import './index.css'

const path = window.location.pathname

function Root() {
  if (path === '/opt-in')  return <OptIn />
  if (path === '/privacy') return <PrivacyPolicy />
  if (path === '/terms')   return <Terms />
  return <App />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
)
