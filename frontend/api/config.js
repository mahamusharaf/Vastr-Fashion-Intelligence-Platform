export default function handler(req, res) {
  res.setHeader('Content-Type', 'application/json');
  res.status(200).json({
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'https://maha1326-vastr-fashion-api.hf.space/api/v1'
  });
}
