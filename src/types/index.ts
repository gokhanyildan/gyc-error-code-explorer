export type PlatformType =
  | 'windows'
  | 'linux'
  | 'web'
  | 'network'
  | 'database'
  | 'container'
  | 'smtp';

export interface ErrorCode {
  code: string;
  codeInt: number;
  name: string;
  description: string;
  platform: PlatformType;
  source: string;
  solutionHint?: string;
  likelySeenIn?: string[];
  runbook?: {
    causes: string[];
    fixCommand?: string;
    deepDive?: string;
  };
  products?: string[]; // <-- Build hatasını çözen kritik alan
}