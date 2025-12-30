import { useState, useEffect } from 'react';
import axios from 'axios';
import { Artist } from './types';

const ReleaseForm = ({ onReleaseCreated }: { onReleaseCreated: () => void }) => {
  const [title, setTitle] = useState('');
  const [artistId, setArtistId] = useState('');
  const [artists, setArtists] = useState<Artist[]>([]);

  useEffect(() => {
    const fetchArtists = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/artists');
        setArtists(response.data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchArtists();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:8000/api/releases', { title, artist_id: artistId });
      setTitle('');
      setArtistId('');
      onReleaseCreated();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Título del release"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />
      <select
        value={artistId}
        onChange={(e) => setArtistId(e.target.value)}
        required
      >
        <option value="">Seleccionar artista</option>
        {artists.map((artist) => (
          <option key={artist.id} value={artist.id}>
            {artist.name} ({artist.type})
          </option>
        ))}
      </select>
      <button type="submit">Crear Release</button>
    </form>
  );
};

export default ReleaseForm;