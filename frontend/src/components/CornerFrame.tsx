function CornerPiece({ style, flip }: { style: React.CSSProperties; flip?: string }) {
  return (
    <svg
      className="corner"
      style={{ ...style, transform: flip }}
      width="13"
      height="13"
      viewBox="0 0 13 13"
      fill="none"
    >
      <path d="M1 12V3L3 1H12" stroke="#8A7245" strokeWidth="1.2" />
      <circle cx="1" cy="12" r="1.3" fill="#8A7245" />
    </svg>
  )
}

export default function CornerFrame() {
  return (
    <>
      <CornerPiece style={{ top: 2, left: 2 }} />
      <CornerPiece style={{ top: 2, right: 2 }} flip="scaleX(-1)" />
      <CornerPiece style={{ bottom: 2, left: 2 }} flip="scaleY(-1)" />
      <CornerPiece style={{ bottom: 2, right: 2 }} flip="scale(-1,-1)" />
    </>
  )
}
