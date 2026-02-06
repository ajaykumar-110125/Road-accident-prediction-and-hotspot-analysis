import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { getDistance } from 'geolib';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

// serve static frontend from public/
app.use(express.static(path.join(__dirname, 'public')));

// load dataset
const roadsPath = path.join(__dirname, 'roads.json');
let roads = [];
try {
  const raw = fs.readFileSync(roadsPath, 'utf8');
  roads = JSON.parse(raw);
  console.log(`Loaded ${roads.length} road/hazard points`);
} catch (err) {
  console.error('Failed to load roads.json - create the file with sample data', err);
}

// utility: find nearest road/hazard for a point
function findNearest(lat, lng) {
  if (!roads || roads.length === 0) return null;
  let best = null;
  let bestDist = Infinity;
  for (const r of roads) {
    const d = getDistance({ latitude: lat, longitude: lng }, { latitude: r.lat, longitude: r.lng });
    if (d < bestDist) {
      bestDist = d;
      best = r;
    }
  }
  return { nearest: best, dist_m: bestDist };
}

// GET safety for single point
app.get('/api/safety', (req, res) => {
  const lat = parseFloat(req.query.lat);
  const lng = parseFloat(req.query.lng);
  if (Number.isNaN(lat) || Number.isNaN(lng)) {
    return res.status(400).json({ error: 'lat and lng required' });
  }
  const found = findNearest(lat, lng);
  if (!found) return res.json({ score: 50 });
  // return the nearest score and distance
  return res.json({ score: found.nearest.score, nearest: found.nearest, dist_m: found.dist_m });
});

// POST bulk: { points: [ {lat,lng}, ... ] }
app.post('/api/safety/bulk', (req, res) => {
  const points = req.body.points;
  if (!Array.isArray(points)) return res.status(400).json({ error: 'points array required' });
  const out = points.map(p => {
    const lat = parseFloat(p.lat);
    const lng = parseFloat(p.lng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) return { lat: p.lat, lng: p.lng, error: 'invalid' };
    const f = findNearest(lat, lng);
    if (!f || !f.nearest) return { lat, lng, score: 50 };
    return { lat, lng, score: f.nearest.score, nearest: f.nearest, dist_m: f.dist_m };
  });
  return res.json({ result: out });
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Safe Route Finder server listening on http://localhost:${port}`));
