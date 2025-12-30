import { useEffect, useState } from 'react';
import axios from 'axios';
import { Artist } from './types';

const ArtistList = ({ refresh }: { refresh: number }) => {
  const [artists, setArtists] = useState<Artist[]>([]);

  const fetchArtists = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/artists');
      setArtists(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchArtists();
  }, [refresh]);

  return (
    <div>
      <h2>Artistas</h2>
      <ul>
        {artists.map((artist) => (
          <li key={artist.id}>
            {artist.name} - {artist.type}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ArtistList;