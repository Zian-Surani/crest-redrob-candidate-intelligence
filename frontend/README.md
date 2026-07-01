# CREST Frontend

React 19 + Vite recruiter intelligence interface. The existing visual system is preserved: light slate surfaces, blue primary actions, premium 32 px cards, the existing sidebar layout, typography, shadows, and Framer Motion transitions.

Representative UI screenshots and short presentation captions are documented in [`../images/README.md`](../images/README.md). The most important screens for judging are the overview dashboard, candidate evidence drawer, pipeline board, analytics readiness page, flagged-profile audit, and landing page.

```powershell
npm install
npm run dev
```

Use `VITE_API_URL` only when the API is hosted separately. Local development uses the Vite `/api` proxy configured in `vite.config.js`.

Validation:

```powershell
npm run lint
npm run build
```
