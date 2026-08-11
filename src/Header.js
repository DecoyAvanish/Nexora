import React from 'react'
import Logo from './robinhood.svg'
import './Header.css'

function Header() {
  return (
    <div className = "wrapper">
      <div className = "logo">
        <img src = {Logo} width = {25} />
      </div>
      <div className = "searchbar">
        <div className = "searchcontainer">
            <input placeholder = "Search" type = "text" />
        </div>
      </div>
      <div className = "menu">
        <a href = '#'>Stocks</a>
        <a href = '#'>Portfolio</a>
        <a href = '#'>Cash</a>
        <a href = '#'>Messages</a>
        <a href = '#'>Account</a>
      </div>
    </div>
  )
}

export default Header
