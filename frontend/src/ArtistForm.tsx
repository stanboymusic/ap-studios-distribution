import { useState } from 'react';
import axios from 'axios';

const ArtistForm = ({ onArtistCreated }: { onArtistCreated: () => void }) => {
  const [name, setName] = useState('');
  const [type, setType] = useState('SOLO');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://127.0.0.1:8000/api/artists', { name, type });
      setName('');
      onArtistCreated();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Nombre del artista"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
      />
      <select
        aria-label="Tipo de artista"
        value={type}
        onChange={(e) => setType(e.target.value)}
      >
        <option value="SOLO">SOLO</option>
        <option value="GROUP">GROUP</option>
      </select>
      <button type="submit">Crear Artista</button>
    </form>
  );
};

export default ArtistForm;