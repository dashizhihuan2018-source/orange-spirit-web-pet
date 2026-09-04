export type WebPetState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'success' | 'error' | 'sleeping'

export type PetAction = 'Idle' | 'Blink' | 'Listen' | 'Think' | 'Speak' | 'Wave' | 'Celebrate' | 'Error' | 'Sleep' | 'Bounce' | 'Spin' | 'Shy' | 'Mischief'

export type PetDefinition = {
  id: string
  name: string
  modelPath: string
  placeholder: string
  accent: string
  accentDark: string
  modelScale?: number
  camera?: [number, number, number]
}

export type WebPetAdapters = {
  transcribe?(audio: Blob, signal?: AbortSignal): Promise<string>
  chat?(text: string, onDelta: (text: string) => void, signal?: AbortSignal): Promise<void>
  synthesize?(text: string, signal?: AbortSignal): Promise<Blob>
}

export type WebPetMountOptions = {
  target: HTMLElement
  adapters?: WebPetAdapters
  assetBaseUrl?: string
  bridgeUrl?: string
}

export type WebPetPlugin = {
  mount(options: WebPetMountOptions): Promise<void>
  unmount(): Promise<void>
  show(): void
  hide(): void
  setState(state: WebPetState): void
  playAction(name: PetAction): boolean
  startListening(): Promise<void>
  stopListening(): void
  speak(input: { text: string; audioUrl?: string }): Promise<void>
}
