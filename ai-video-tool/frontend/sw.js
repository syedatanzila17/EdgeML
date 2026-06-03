'use strict';

const CACHE = 'videoai-v1';
const PRECACHE = ['/', '/styles.css', '/app.js', '/manifest.json', '/icon.svg'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Pass API requests through, never cache them
  if (url.pathname.startsWith('/api/')) return;

  // Network-first for navigation, cache-first for assets
  const strategy = e.request.mode === 'navigate'
    ? networkFirst(e.request)
    : cacheFirst(e.request);

  e.respondWith(strategy);
});

async function networkFirst(req) {
  try {
    const resp = await fetch(req);
    if (resp.ok) {
      const cache = await caches.open(CACHE);
      cache.put(req, resp.clone());
    }
    return resp;
  } catch {
    return caches.match(req) || caches.match('/');
  }
}

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const resp = await fetch(req);
    if (resp.ok) {
      const cache = await caches.open(CACHE);
      cache.put(req, resp.clone());
    }
    return resp;
  } catch {
    return new Response('Offline', { status: 503 });
  }
}
