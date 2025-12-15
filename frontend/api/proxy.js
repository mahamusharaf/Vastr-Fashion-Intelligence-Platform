// api/proxy.js
export default async function handler(req, res) {
    // Only allow GET requests
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    // Get the target URL from query params
    const targetUrl = req.query.url;
    
    if (!targetUrl) {
        return res.status(400).json({ error: 'Missing url parameter' });
    }

    // Verify it's our HuggingFace API
    if (!targetUrl.includes('maha1326-vastr-fashion-api.hf.space')) {
        return res.status(403).json({ error: 'Invalid target URL' });
    }

    try {
        // Fetch from HuggingFace API
        const apiResponse = await fetch(targetUrl, {
            headers: {
                'Accept': 'application/json',
            },
        });

        if (!apiResponse.ok) {
            throw new Error(`API responded with ${apiResponse.status}`);
        }

        const data = await apiResponse.json();

        // Set CORS headers
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET');
        res.setHeader('Content-Type', 'application/json');

        // Return the data
        return res.status(200).json(data);

    } catch (error) {
        console.error('Proxy error:', error);
        return res.status(500).json({ 
            error: 'Failed to fetch from API',
            details: error.message 
        });
    }
}
