import logo from './logo.svg';
import './App.css';
import Header from './Header'
import Feed from './Feed'
import Stats from './Stats'

function App() {
  return (
    <div className="App">
      <div className = "header">
        <Header />
      </div>
      <div className = "body">
        <div className = "info">
          <Feed />
          <Stats />
        </div>
      </div>
    </div>
  );
}

export default App;
