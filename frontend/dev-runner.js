import { createServer } from 'vite';

async function start() {
  const server = await createServer({
    configFile: './vite.config.ts',
    server: {
      host: '127.0.0.1',
      port: 5173,
    },
  });
  await server.listen();
  console.log('Vite Dev Server live on http://127.0.0.1:5173');
  // Keep process alive indefinitely
  setInterval(() => {}, 1 << 30);
}

start().catch((err) => {
  console.error('Failed to start Vite dev server:', err);
  process.exit(1);
});
