import type {
  BiometricData,
  EnvironmentData,
  RecommendationOutput,
  UserPreferences,
} from '@/lib/types'
import { fromFinalOutput, toAgent1Input } from './adapter'
import { getJson, postJson } from './client'
import type {
  Agent1Input,
  FinalOutput,
  Ingredient,
  IngredientsResponse,
} from './schemas'

export async function generatePerfume(
  preferences: UserPreferences,
  biometrics: BiometricData,
  environment: EnvironmentData,
): Promise<{ recommendation: RecommendationOutput; raw: FinalOutput }> {
  const payload = toAgent1Input(preferences, biometrics, environment)
  const raw = await postJson<Agent1Input, FinalOutput>('/api/generate-perfume', payload)
  const recommendation = fromFinalOutput(raw, preferences, biometrics, environment)
  return { recommendation, raw }
}

export async function fetchIngredients(): Promise<Ingredient[]> {
  const res = await getJson<IngredientsResponse>('/api/ingredients')
  return res.ingredients ?? []
}
