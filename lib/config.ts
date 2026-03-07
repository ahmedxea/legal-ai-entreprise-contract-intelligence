/**
 * Runtime configuration for the Lexra frontend.
 *
 * All environment-specific values must be read here.
 * Consumers import from this module; they do not read process.env directly.
 */

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
} as const
