import React from 'react'
import './Chip.css'

function Chip({ label, icon }) {
    return (
        <div className="chip">
            <div className="avatar">
                {icon}
            </div>
            <div className="label">   
                <span>{label}</span>
            </div>
        </div>
    )
}

export default Chip;