import type { CSSProperties, ReactNode } from 'react'
import './WoodenBoard.css'

// the light parchment content box that sits inside PanelDark on login/create-semester
export default function WoodenBoard({
    children,
    style,
}: {
    children: ReactNode
    style?: CSSProperties
}) {
    return (
        <div className="bg-wooden wooden-board" style={style}>
            <div className="bg-wooden-left">

            </div>
            <div className="bg-wooden-right">

            </div>
            {children}
        </div>
    )
}
