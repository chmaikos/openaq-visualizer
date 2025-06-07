/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_MQTT_WS_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'mqtt/dist/mqtt.js' {
  import { MqttClient } from 'mqtt'
  export * from 'mqtt'
  export default mqtt
} 