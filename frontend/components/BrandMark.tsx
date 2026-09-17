/** Premium AcademicCheck monogram — ink seal + teal diagnostic check. */
export function BrandMark({
  className = "h-8 w-8",
  animated = false,
}: {
  className?: string;
  animated?: boolean;
}) {
  return (
    <svg
      className={`${className}${animated ? " ac-brand-float" : ""}`}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <rect width="64" height="64" rx="14" fill="#0B1220" />
      <rect
        x="1.25"
        y="1.25"
        width="61.5"
        height="61.5"
        rx="12.75"
        stroke="#0F766E"
        strokeOpacity="0.45"
        strokeWidth="1.5"
      />
      <path
        d="M32 14L18 50h6.2l3.1-8.2h9.4L39.8 50H46L32 14zm-3.2 22.4L32 24.2l3.2 12.2h-6.4z"
        fill="#F4F6F8"
      />
      <path
        className={animated ? "ac-check-animated" : undefined}
        d="M22.5 33.5L29 40l13.5-16"
        stroke="#0F766E"
        strokeWidth="3.25"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
