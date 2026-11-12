import { useEffect, useState } from 'react'
import { HomeScreen } from './screens/HomeScreen'
import { PlayScreen } from './screens/PlayScreen'
import { ClientRoute } from './screens/ClientRoute'
import { isClientHash } from './services/share'
import { emptyDraft } from './types/client'
import type { ClientDraft } from './types/client'
import './App.css'

type Screen = 'home' | 'play'

function App() {
  const [screen, setScreen] = useState<Screen>('home')
  const [draft, setDraft] = useState<ClientDraft>(emptyDraft)
  const [hash, setHash] = useState(window.location.hash)

  useEffect(() => {
    const onHash = () => setHash(window.location.hash)
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  if (isClientHash(hash)) return <ClientRoute />

  return screen === 'home' ? (
    <HomeScreen draft={draft} onChange={setDraft} onStart={() => setScreen('play')} />
  ) : (
    <PlayScreen client={draft} onBack={() => setScreen('home')} />
  )
}

export default App
