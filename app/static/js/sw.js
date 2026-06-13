const CACHE_NAME = 'controldesk-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/login',
  '/index',
  '/static/js/dashboard.js',
  '/static/sounds/lana_asistente.mp3',
  '/static/images/agricultura.png',
  '/static/images/apicultura.png',
  '/static/images/ferreteria.png'
];

// Instalar y almacenar en caché recursos estáticos básicos
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching app shell');
      // Usamos map y catches individuales por si alguna ruta da 404 para que no falle todo el cache
      return Promise.allSettled(
        ASSETS_TO_CACHE.map(url => {
          return cache.add(url).catch(err => {
            console.warn(`[Service Worker] Failed to cache asset: ${url}`, err);
          });
        })
      );
    })
  );
  self.skipWaiting();
});

// Activar y limpiar cachés antiguas
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[Service Worker] Clearing old cache', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Interceptar peticiones de red
self.addEventListener('fetch', (event) => {
  // Ignorar peticiones no-GET
  if (event.request.method !== 'GET') {
    return;
  }

  const requestUrl = new URL(event.request.url);

  // 1. Ignorar endpoints de API y debug de Flask (ir siempre directo a red)
  if (requestUrl.pathname.startsWith('/api/') || requestUrl.pathname.startsWith('/_/') || requestUrl.hostname === 'localhost' && requestUrl.port === '35729') {
    return;
  }

  // 2. Recursos externos de CDN (Tailwind CSS, Font Awesome, Google Fonts)
  // Estrategia: Cache First con fallback a red
  if (
    event.request.url.includes('tailwindcss.com') ||
    event.request.url.includes('cloudflare.com') ||
    event.request.url.includes('googleapis.com') ||
    event.request.url.includes('gstatic.com')
  ) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        }).catch((err) => {
          console.warn('[Service Worker] CDN fetch failed and no cache available', err);
          return new Response('Offline resource not cached', { status: 503, statusText: 'Offline' });
        });
      })
    );
    return;
  }

  // 3. Archivos estáticos locales (bajo /static/)
  // Estrategia: Cache First con fallback a red
  if (requestUrl.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        });
      })
    );
    return;
  }

  // 4. Páginas HTML de la aplicación (Navegación)
  // Estrategia: Network First con fallback a Cache y finalmente fallback a /login
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        // Guardar la página en caché si la respuesta es correcta
        if (networkResponse && networkResponse.status === 200) {
          const responseClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        // En caso de estar desconectado, buscar en la caché
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Si no está la página en caché, intentar servir el login o index
          return caches.match('/login') || caches.match('/index');
        });
      })
  );
});
