# Slon Desktop

Tauri v2 + React + TypeScript shell for the next Slon desktop UI.

The legacy PyQt UI remains in the repository while this shell reaches feature parity.

## Development

Install JavaScript dependencies:

```sh
npm install
```

Run the frontend only:

```sh
npm run dev
```

Run the Tauri app after installing Rust and Tauri prerequisites:

```sh
npm run tauri:dev
```

Start the Python backend in another terminal when backend health/status integration is needed:

```sh
cd ../..
python -m server --host 127.0.0.1 --port 8765
```

The UI handles offline and unauthorized backend states explicitly. Secrets remain backend-owned and must not be persisted by the frontend.