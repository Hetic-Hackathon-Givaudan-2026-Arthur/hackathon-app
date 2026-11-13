import type { ReactNode, SVGProps } from 'react';

type IconName =
  | 'sparkles'
  | 'mic'
  | 'play'
  | 'pause'
  | 'stop'
  | 'x'
  | 'refresh'
  | 'layers'
  | 'wave'
  | 'user'
  | 'search'
  | 'check'
  | 'arrow-left'
  | 'database'
  | 'video'
  | 'present'
  | 'hangup'
  | 'quote'
  | 'share'
  | 'download'
  | 'chevron-left'
  | 'chevron-right'
  | 'edit';

const paths: Record<IconName, ReactNode> = {
  sparkles: (
    <>
      <path d="m12 3 1.9 6.1L20 11l-6.1 1.9L12 19l-1.9-6.1L4 11l6.1-1.9L12 3Z" />
      <path d="m19 18 .65 1.35L21 20l-1.35.65L19 22l-.65-1.35L17 20l1.35-.65L19 18Z" />
    </>
  ),
  mic: (
    <>
      <rect x="9" y="2.5" width="6" height="12" rx="3" />
      <path d="M5.5 10.5a6.5 6.5 0 0 0 13 0M12 17v4m-4 0h8" />
    </>
  ),
  play: <path d="m8 5 11 7-11 7V5Z" />,
  pause: (
    <>
      <path d="M8 5v14M16 5v14" strokeWidth="3" />
    </>
  ),
  stop: <rect x="6" y="6" width="12" height="12" rx="3" />,
  x: <path d="M6 6 18 18M18 6 6 18" />,
  refresh: (
    <>
      <path d="M20 11a8 8 0 1 0-2 6" />
      <path d="m20 4 0 7-7 0" />
    </>
  ),
  layers: (
    <>
      <path d="m12 3 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5M3 16l9 5 9-5" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-4-4" />
    </>
  ),
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  'arrow-left': <path d="M19 12H5m6-6-6 6 6 6" />,
  database: (
    <>
      <ellipse cx="12" cy="6" rx="7.5" ry="3" />
      <path d="M4.5 6v12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3V6M4.5 12c0 1.7 3.4 3 7.5 3s7.5-1.3 7.5-3" />
    </>
  ),
  video: (
    <>
      <rect x="3" y="6.5" width="12" height="11" rx="2.5" />
      <path d="m15 11 6-3.5v9L15 13" />
    </>
  ),
  present: (
    <>
      <rect x="3" y="4.5" width="18" height="12" rx="2" />
      <path d="M12 19.5v-3m0 0-2.5 2.5M12 16.5l2.5 2.5" />
    </>
  ),
  hangup: (
    <path d="M3.5 14.5c5-4.5 12-4.5 17 0l-2 3-3.5-1.5v-2.5c-2-.8-4-.8-6 0v2.5L5.5 17.5l-2-3Z" />
  ),
  quote: (
    <>
      <path d="M10 7H6.5A1.5 1.5 0 0 0 5 8.5V12h4v5H4" />
      <path d="M19 7h-3.5A1.5 1.5 0 0 0 14 8.5V12h4v5h-5" />
    </>
  ),
  share: (
    <>
      <path d="M12 15V3m0 0L8 7m4-4 4 4" />
      <path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7" />
    </>
  ),
  download: (
    <>
      <path d="M12 3v12m0 0-4-4m4 4 4-4" />
      <path d="M5 15v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4" />
    </>
  ),
  'chevron-left': <path d="m15 5-7 7 7 7" />,
  'chevron-right': <path d="m9 5 7 7-7 7" />,
  edit: (
    <>
      <path d="M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3Z" />
      <path d="m13.5 8.5 3 3" />
    </>
  ),
  wave: (
    <>
      <path d="M3 9v6M7 5v14M11 8v8M15 3v18M19 7v10M23 10v4" />
    </>
  ),
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 18, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {paths[name]}
    </svg>
  );
}
