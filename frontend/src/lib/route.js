import { useEffect, useState } from 'react'

// Three screens, addressed by a plain #name so links work everywhere, including a claude.ai artifact:
//   (none) home   #fit the measurement quiz   #results recommendations
export const ROUTES = ['home', 'fit', 'results']

function current() {
  const name = window.location.hash.replace(/^#/, '')
  return ROUTES.includes(name) ? name : 'home'
}

export function go(route) {
  const hash = route === 'home' ? '' : `#${route}`
  if (window.location.hash !== hash) {
    if (hash) window.location.hash = hash
    else history.pushState(null, '', window.location.pathname + window.location.search)
  }
  window.dispatchEvent(new HashChangeEvent('hashchange'))
  window.scrollTo(0, 0)
}

export function useRoute() {
  const [route, setRoute] = useState(current)
  useEffect(() => {
    const on = () => setRoute(current())
    window.addEventListener('hashchange', on)
    window.addEventListener('popstate', on)
    return () => {
      window.removeEventListener('hashchange', on)
      window.removeEventListener('popstate', on)
    }
  }, [])
  return route
}
