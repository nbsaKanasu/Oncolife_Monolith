require('dotenv').config();
const express = require('express');
const cookieParser = require('cookie-parser');
const configureMiddleware = require('./config/config.middleware');
const { createWsProxies } = require('./config/config.middleware');
const routes = require('./routes');

const app = express();

// Configure basic middleware (CORS, body parsing, etc.)
app.use(require('cors')({
  origin: ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true
}));

if (process.env.NODE_ENV !== 'test') {
  app.use(require('morgan')('combined'));
}

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(cookieParser());

// Mount Express API routes FIRST (these take precedence over proxy)
app.use('/api', routes);

// Configure proxy middleware (for routes not handled by Express)
configureMiddleware(app);

// 404 handler for API routes only
app.use('/api/*', (req, res) => {
  res.status(404).json({
    error: 'API route not found',
    path: req.originalUrl,
    method: req.method
  });
});

const PORT = process.env.PORT || 3000;

// Start server
const server = app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🌐 URL: http://localhost:${PORT}`);
});

// Ensure WS upgrade requests are proxied when hitting this gateway directly
const { wsProxyNoRewrite, wsProxyWithRewrite } = createWsProxies();
server.on('upgrade', (req, socket, head) => {
  const url = req.url || '';
  console.log(`[SERVER UPGRADE] WebSocket upgrade request: ${url}`);
  console.log(`[SERVER UPGRADE] Request headers:`, JSON.stringify(req.headers, null, 2));
  
  if (url.startsWith('/api/chat/ws')) {
    console.log(`[SERVER UPGRADE] Routing /api/chat/ws request through wsProxyWithRewrite`);
    // Manually rewrite path for upgrade requests to match FastAPI route
    req.url = url.replace(/^\/api\/chat\/ws/, '/chat/ws');
    console.log(`[SERVER UPGRADE] Rewritten URL: ${req.url}`);
    
    // CRITICAL: Inject Authorization header from authToken cookie (since upgrade bypasses middleware)
    try {
      const cookieHeader = req.headers && req.headers.cookie;
      console.log(`[SERVER UPGRADE] Cookie header present: ${!!cookieHeader}`);
      
      if (cookieHeader) {
        console.log(`[SERVER UPGRADE] Cookie header: ${cookieHeader.substring(0, 100)}...`);
        const authMatch = cookieHeader.match(/(?:^|;\s*)authToken=([^;]+)/);
        console.log(`[SERVER UPGRADE] authToken match: ${!!authMatch}`);
        
        if (authMatch && authMatch[1]) {
          const token = decodeURIComponent(authMatch[1]);
          console.log(`[SERVER UPGRADE] Decoded token length: ${token.length}`);
          console.log(`[SERVER UPGRADE] Token preview: ${token.substring(0, 50)}...`);
          req.headers.authorization = `Bearer ${token}`;
          console.log('[SERVER UPGRADE] ✅ Injected Authorization header from authToken cookie');
        } else {
          console.log('[SERVER UPGRADE] ❌ No authToken found in cookies');
        }
      } else {
        console.log('[SERVER UPGRADE] ❌ No cookie header found');
      }
    } catch (e) {
      console.error('[SERVER UPGRADE] Error injecting auth header:', e);
    }
    
    wsProxyWithRewrite.upgrade(req, socket, head);
  } else if (url.startsWith('/chat/ws')) {
    console.log(`[SERVER UPGRADE] Routing /chat/ws request through wsProxyNoRewrite`);
    wsProxyNoRewrite.upgrade(req, socket, head);
  } else {
    console.log(`[SERVER UPGRADE] ❌ No matching WebSocket route for: ${url}`);
    socket.end();
  }
});

// Graceful shutdown
const gracefulShutdown = (signal) => {
  console.log(`${signal} received, shutting down gracefully`);
  server.close(() => {
    console.log('Process terminated');
    process.exit(0);
  });
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

module.exports = server;