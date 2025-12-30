import { useState } from 'react'
import './App.css'
import ArtistForm from './ArtistForm'
import ReleaseForm from './ReleaseForm'
import ArtistList from './ArtistList'
import ReleaseList from './ReleaseList'

function App() {
  const [artistRefresh, setArtistRefresh] = useState(0);
  const [releaseRefresh, setReleaseRefresh] = useState(0);

  return (
    <div className="App">
      <h1>AP Studios Distribution</h1>
      <ArtistForm onArtistCreated={() => setArtistRefresh(prev => prev + 1)} />
      <ArtistList refresh={artistRefresh} />
      <ReleaseForm onReleaseCreated={() => setReleaseRefresh(prev => prev + 1)} />
      <ReleaseList refresh={releaseRefresh} />
    </div>
  )
}

export default App