import { useEffect, useState } from 'react'

type BeforeInstallPromptEvent = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }> }
function isStandalone(): boolean {
  if (window.matchMedia('(display-mode: standalone)').matches) return true
  return Boolean((window.navigator as { standalone?: boolean }).standalone)
}
function isIos(): boolean { return /iphone|ipad|ipod/i.test(window.navigator.userAgent) }

export function InstallPrompt() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [standalone, setStandalone] = useState(false)
  useEffect(() => {
    setStandalone(isStandalone())
    const onPrompt = (event: Event) => { event.preventDefault(); setDeferred(event as BeforeInstallPromptEvent) }
    window.addEventListener('beforeinstallprompt', onPrompt)
    return () => window.removeEventListener('beforeinstallprompt', onPrompt)
  }, [])
  if (standalone || dismissed) return null
  if (deferred) return <div className="morning-install-banner"><span>Install Morning for quicker access on shift.</span><div className="morning-install-actions"><button type="button" className="primary" onClick={() => void deferred.prompt().then(() => setDeferred(null))}>Install</button><button type="button" onClick={() => setDismissed(true)}>Not now</button></div></div>
  if (isIos()) return <div className="morning-install-banner"><span>Add Morning to your Home Screen: tap Share, then “Add to Home Screen”.</span><button type="button" onClick={() => setDismissed(true)}>Got it</button></div>
  return null
}
