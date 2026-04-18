import type {
  BiometricData,
  EnvironmentData,
  RecommendationOutput,
  UserPreferences,
} from '@/lib/types'
import { fromFinalOutput, toAgent1Input } from './adapter'
import { postJson } from './client'
import type { Agent1Input, FinalOutput } from './schemas'

export async function generatePerfume(
  preferences: UserPreferences,
  biometrics: BiometricData,
  environment: EnvironmentData,
): Promise<RecommendationOutput> {
  const payload = toAgent1Input(preferences, biometrics, environment)
  const final = await postJson<Agent1Input, FinalOutput>('/api/generate-perfume', payload)
  return fromFinalOutput(final, preferences, biometrics, environment)
}
