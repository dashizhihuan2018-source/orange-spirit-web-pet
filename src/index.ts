import type { PetDefinition, WebPetPlugin } from './contracts'
import { ORANGE_SPIRIT } from './pets/orangeSpirit'
import { createPetRuntime } from './runtime/createPetRuntime'

export type { PetAction, PetDefinition, WebPetAdapters, WebPetMountOptions, WebPetPlugin, WebPetState } from './contracts'
export { ORANGE_SPIRIT } from './pets/orangeSpirit'

export function createWebPetPlugin(definition: PetDefinition = ORANGE_SPIRIT): WebPetPlugin {
  return createPetRuntime(definition)
}
