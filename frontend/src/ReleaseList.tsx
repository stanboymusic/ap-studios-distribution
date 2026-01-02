import { useEffect, useState } from 'react';
import axios from 'axios';
import { Release } from './types';

const ReleaseList = ({ refresh }: { refresh: number }) => {
  const [releases, setReleases] = useState<Release[]>([]);

  const fetchReleases = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/releases/');
      setReleases(response.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchReleases();
  }, [refresh]);

  return (
    <div>
      <h2>Releases</h2>
      <ul>
        {releases.map((release) => (
          <li key={release.id}>
            {release.title} - {release.type} - {release.status}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ReleaseList;