export type PlatformType = 'windows' | 'linux' | 'mac';

export interface ErrorCode {
  code: string;
  codeInt: number;
  name: string;
  description: string;
  platform: PlatformType;
  source: string;
  solutionHint?: string;
}
