import { useEffect, useState } from 'react'
import { api } from './lib/api'
import { hasMeasurements, loadIntent, loadProfile, saveIntent, saveProfile } from './lib/profile'
import { go, useRoute } from './lib/route'
import Home from './pages/Home'
import Quiz from './pages/Quiz'
import Results from './pages/Results'

// Three screens: a branded home page, a one-question-at-a-time quiz, and the recommendations.
export default function App() {
  const route = useRoute()
  const [profile, setProfile] = useState(loadProfile)
  const [intent, setIntent] = useState(loadIntent)
  const [meta, setMeta] = useState(null)

  useEffect(() => saveProfile(profile), [profile])
  useEffect(() => saveIntent(intent), [intent])
  useEffect(() => {
    api.meta().then(setMeta).catch(() => {})
  }, [])

  if (route === 'fit') {
    return (
      <Quiz
        profile={profile}
        intent={intent}
        categories={meta?.categories || []}
        onDone={(p, w) => {
          setProfile(p)
          setIntent(w)
          go('results')
        }}
      />
    )
  }
  if (route === 'results') {
    return <Results profile={profile} onProfile={setProfile} intent={intent} onIntent={setIntent} meta={meta} />
  }
  return <Home meta={meta} hasProfile={hasMeasurements(profile)} />
}
