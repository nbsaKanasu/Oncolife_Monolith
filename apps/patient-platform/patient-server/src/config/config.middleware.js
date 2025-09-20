const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { createProxyMiddleware } = require('http-proxy-middleware');

// Helper to build WS proxies
function createWsProxies() {
  const rawBackendBase = process.env.BACKEND_URL;
  const backendBase = (typeof rawBackendBase === 'string' ? rawBackendBase.trim() : '') || 'http://localhost:8000';

  const common = {
    target: backendBase,
    changeOrigin: true,
    ws: true,
    xfwd: true,
    onProxyReq: (proxyReq, req, res) => {
      console.log(`[WS Proxy] ${req.method} ${req.url} -> ${backendBase}`);
    },
    onProxyReqWs: (proxyReq, req, socket, options, head) => {
      try {
        console.log(`[WS Proxy] onProxyReqWs called for ${req.url}`);
        console.log(`[WS Proxy] Request headers:`, JSON.stringify(req.headers, null, 2));
        
        // Forward Authorization from cookies if present (HTTP-only cookie authToken)
        const cookieHeader = req.headers && req.headers.cookie;
        console.log(`[WS Proxy] Cookie header present: ${!!cookieHeader}`);
        
        if (cookieHeader) {
          console.log(`[WS Proxy] Cookie header: ${cookieHeader}`);
          const authMatch = cookieHeader.match(/(?:^|;\s*)authToken=([^;]+)/);
          console.log(`[WS Proxy] authToken match: ${!!authMatch}`);
          
          if (authMatch && authMatch[1]) {
            const token = decodeURIComponent(authMatch[1]);
            console.log(`[WS Proxy] Decoded token length: ${token.length}`);
            console.log(`[WS Proxy] Token preview: ${token.substring(0, 50)}...`);
            proxyReq.setHeader('Authorization', `Bearer ${token}`);
            console.log('[WS Proxy] ✅ Injected Authorization header from authToken cookie');
          } else {
            console.log('[WS Proxy] ❌ No authToken found in cookies');
          }
        } else {
          console.log('[WS Proxy] ❌ No cookie header found');
        }
        
        console.log(`[WS Proxy] Final proxy request headers:`, JSON.stringify(proxyReq.getHeaders(), null, 2));
      } catch (e) {
        console.error('[WS Proxy] onProxyReqWs error:', e);
      }
    },
    onError: (err, req, res) => {
      console.error('[WS Proxy] error:', err);
    }
  };

  const wsProxyNoRewrite = createProxyMiddleware(common);
  const wsProxyWithRewrite = createProxyMiddleware({
    ...common,
    pathRewrite: {
      '^/api/chat/ws': '/chat/ws'
    }
  });

  return { wsProxyNoRewrite, wsProxyWithRewrite };
}

// Main configuration function
function configureMiddleware(app) {
  const connectSrc = process.env.NODE_ENV === 'production'
    ? ["'self'", 'https:', 'wss:']
    : ["'self'", 'http:', 'https:', 'ws:', 'wss:'];

  app.use(helmet({
    contentSecurityPolicy: {
      useDefaults: true,
      directives: {
        "default-src": ["'self'"],
        "img-src": ["'self'", 'data:', 'https://cdn.jsdelivr.net'],
        "connect-src": connectSrc,
      }
    }
  }));

  app.use(cors({
    origin: process.env.CORS_ORIGIN || ['http://localhost:3000', 'http://localhost:5173'],
    credentials: true
  }));

  if (process.env.NODE_ENV !== 'test') {
    app.use(morgan('combined'));
  }

  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // Always proxy WebSocket connections to FastAPI backend
  const { wsProxyNoRewrite, wsProxyWithRewrite } = createWsProxies();

  // Support both '/chat/ws' and '/api/chat/ws' so BASE_URL can be '/api'
  app.use('/chat/ws', wsProxyNoRewrite);
  app.use('/api/chat/ws', wsProxyWithRewrite);
  
  console.log('[MIDDLEWARE] WebSocket proxies configured:');
  console.log('[MIDDLEWARE] - /chat/ws -> wsProxyNoRewrite');
  console.log('[MIDDLEWARE] - /api/chat/ws -> wsProxyWithRewrite');

  if (process.env.NODE_ENV === 'production') {
    const webDist = path.join(__dirname, '../../../patient-web/dist');
    app.use(express.static(webDist));

    // Single Page App fallback to index.html (excluding API and WS routes)
    app.get('*', (req, res, next) => {
      if (req.url.startsWith('/api') || req.url.startsWith('/chat/ws')) return next();
      return res.sendFile(path.join(webDist, 'index.html'));
    });
    return; // No Vite proxy in production
  }

  // ---- Development mode only: proxy frontend requests to Vite dev server ----
  app.use('/', createProxyMiddleware({
    target: 'http://localhost:5173',
    changeOrigin: true,
    pathRewrite: {
      '^/api': '/api'  // Don't rewrite API calls
    },
    onProxyReq: (proxyReq, req, res) => {
      // Only proxy non-API routes to Vite
      if (!req.url.startsWith('/api') && !req.url.startsWith('/chat/ws')) {
        console.log(`Proxying frontend request: ${req.method} ${req.url} to Vite`);
      }
    },
    // Skip proxying for API routes and WebSocket
    filter: (req, res) => {
      return !req.url.startsWith('/api') && !req.url.startsWith('/chat/ws');
    }
  }));
}

module.exports = configureMiddleware;
module.exports.createWsProxies = createWsProxies;